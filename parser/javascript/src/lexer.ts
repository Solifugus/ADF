import { Token, TokenType, AdfError } from './types';

/**
 * Lexer for ADF format - tokenizes line by line
 */
export class Lexer {
  private inMultiline = false;
  private multilineQuoteCount = 0;

  /**
   * Tokenize ADF text into tokens
   */
  tokenize(text: string): Token[] {
    const tokens: Token[] = [];
    const lines = text.split('\n');

    for (let i = 0; i < lines.length; i++) {
      const token = this.tokenizeLine(lines[i], i + 1);
      if (token) {
        tokens.push(token);
      }
    }

    return tokens;
  }

  /**
   * Tokenize a single line
   */
  private tokenizeLine(line: string, lineNumber: number): Token | null {
    // Handle multiline continuation
    if (this.inMultiline) {
      return this.handleMultilineContinuation(line, lineNumber);
    }

    // Blank line
    if (!line.trim()) {
      return {
        type: TokenType.BlankLine,
        lineNumber,
        rawLine: line,
      };
    }

    // Try to parse header
    const headerToken = this.tryParseHeader(line, lineNumber);
    if (headerToken) {
      return headerToken;
    }

    // Key-value pair
    if (line.includes('=')) {
      return this.parseKeyValue(line, lineNumber);
    }

    // Scalar value
    return {
      type: TokenType.ScalarValue,
      lineNumber,
      rawLine: line,
      value: line.trim(),
    };
  }

  /**
   * Try to parse a header line
   */
  private tryParseHeader(line: string, lineNumber: number): Token | null {
    const stripped = line.trim();

    if (!stripped.endsWith(':')) {
      return null;
    }

    let pathPart = stripped.slice(0, -1).trim();
    const isAbsolute = pathPart.startsWith('#');

    if (isAbsolute) {
      pathPart = pathPart.slice(1).trim();
    }

    // Root section
    if (!pathPart && isAbsolute) {
      return {
        type: TokenType.AbsoluteHeader,
        lineNumber,
        rawLine: line,
        path: '',
        isAbsolute: true,
      };
    }

    if (!pathPart) {
      return null;
    }

    if (!this.isValidPath(pathPart)) {
      return null;
    }

    return {
      type: isAbsolute ? TokenType.AbsoluteHeader : TokenType.RelativeHeader,
      lineNumber,
      rawLine: line,
      path: pathPart,
      isAbsolute,
    };
  }

  /**
   * Parse a key=value line
   */
  private parseKeyValue(line: string, lineNumber: number): Token {
    const equalsPos = line.indexOf('=');
    const rawKey = line.slice(0, equalsPos).trim();
    const rawValue = line.slice(equalsPos + 1).trimStart();

    const key = rawKey;

    // Check for multiline value
    const quoteCount = this.countLeadingQuotes(rawValue);
    if (quoteCount > 0) {
      this.inMultiline = true;
      this.multilineQuoteCount = quoteCount;

      // Check if it ends on same line
      if (rawValue.length > quoteCount * 2 && this.endsWithQuotes(rawValue, quoteCount)) {
        // Single-line quoted value
        this.inMultiline = false;
        const value = this.extractQuotedValue(rawValue, quoteCount);
        const constraint = this.extractConstraintAfterQuotes(rawValue, quoteCount);

        return {
          type: TokenType.KeyValue,
          lineNumber,
          rawLine: line,
          key,
          value,
          constraint,
        };
      } else {
        // Multiline start
        const content = rawValue.length > quoteCount ? rawValue.slice(quoteCount) : '';

        return {
          type: TokenType.MultilineStart,
          lineNumber,
          rawLine: line,
          key,
          value: content,
          quoteCount,
        };
      }
    }

    // Simple value
    const { value, constraint } = this.parseValueAndConstraint(rawValue);

    return {
      type: TokenType.KeyValue,
      lineNumber,
      rawLine: line,
      key,
      value,
      constraint,
    };
  }

  /**
   * Handle multiline continuation
   */
  private handleMultilineContinuation(line: string, lineNumber: number): Token {
    if (this.endsWithQuotes(line, this.multilineQuoteCount)) {
      this.inMultiline = false;
      const content = line.length >= this.multilineQuoteCount
        ? line.slice(0, -this.multilineQuoteCount).trimEnd()
        : '';
      const constraint = this.extractConstraintAfterLine(line, this.multilineQuoteCount);

      return {
        type: TokenType.MultilineEnd,
        lineNumber,
        rawLine: line,
        value: content,
        constraint,
      };
    }

    return {
      type: TokenType.MultilineContent,
      lineNumber,
      rawLine: line,
      value: line,
    };
  }

  /**
   * Check if path is valid
   */
  private isValidPath(path: string): boolean {
    if (!path) return true;

    const parts = path.split('.');
    for (const part of parts) {
      // Quoted key
      if (part.startsWith('"') && part.endsWith('"')) {
        continue;
      }
      // Regular key pattern
      if (!/^[A-Za-z0-9_]+$/.test(part)) {
        return false;
      }
    }
    return true;
  }

  /**
   * Count leading quotes
   */
  private countLeadingQuotes(s: string): number {
    let count = 0;
    for (const char of s) {
      if (char === '"') {
        count++;
      } else {
        break;
      }
    }
    return count;
  }

  /**
   * Check if string ends with N quotes
   */
  private endsWithQuotes(s: string, count: number): boolean {
    if (s.length < count) return false;
    return s.slice(-count) === '"'.repeat(count);
  }

  /**
   * Extract value from within quotes
   */
  private extractQuotedValue(s: string, quoteCount: number): string {
    if (s.length < quoteCount * 2) return '';
    return s.slice(quoteCount, -quoteCount);
  }

  /**
   * Extract constraint after quotes
   */
  private extractConstraintAfterQuotes(s: string, quoteCount: number): string | undefined {
    if (s.length <= quoteCount * 2) return undefined;
    const after = s.slice(s.length - quoteCount);
    return this.parseConstraint(after);
  }

  /**
   * Extract constraint after closing quotes on a line
   */
  private extractConstraintAfterLine(line: string, quoteCount: number): string | undefined {
    if (line.length < quoteCount) return undefined;
    const after = line.slice(line.length - quoteCount);
    return this.parseConstraint(after);
  }

  /**
   * Parse value and constraint
   */
  private parseValueAndConstraint(s: string): { value: string; constraint?: string } {
    const constraint = this.parseConstraint(s);
    if (constraint) {
      const parenPos = s.lastIndexOf('(');
      if (parenPos !== -1) {
        const value = s.slice(0, parenPos).trimEnd();
        return { value, constraint };
      }
    }
    return { value: s.trim() };
  }

  /**
   * Parse constraint from string
   */
  private parseConstraint(s: string): string | undefined {
    const trimmed = s.trim();
    if (!trimmed) return undefined;

    const openParen = trimmed.lastIndexOf('(');
    const closeParen = trimmed.lastIndexOf(')');

    if (openParen === -1 || closeParen === -1 || closeParen < openParen) {
      return undefined;
    }

    const constraint = trimmed.slice(openParen + 1, closeParen).trim();
    return constraint || undefined;
  }
}
