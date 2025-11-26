import { Document } from './document';
import { Lexer } from './lexer';
import { Token, TokenType, ParseOptions, Value, AdfError } from './types';

/**
 * Parser for ADF format
 */
export class Parser {
  private inferTypes: boolean;
  private strict: boolean;

  constructor(options: ParseOptions = {}) {
    this.inferTypes = options.inferTypes !== false;
    this.strict = options.strict !== false;
  }

  /**
   * Parse ADF text into a Document
   */
  parse(text: string): Document {
    const lexer = new Lexer();
    const tokens = lexer.tokenize(text);

    const document = new Document();
    this.parseTokens(tokens, document);

    return document;
  }

  /**
   * Parse tokens into document structure
   */
  private parseTokens(tokens: Token[], document: Document): void {
    let i = 0;
    let currentSectionPath = '';
    let currentIsAbsolute = true;
    let sectionStart = 0;

    while (i < tokens.length) {
      const token = tokens[i];

      if (token.type === TokenType.AbsoluteHeader || token.type === TokenType.RelativeHeader) {
        // Process previous section
        if (i > sectionStart) {
          const sectionTokens = tokens.slice(sectionStart, i);
          this.processSection(sectionTokens, currentSectionPath, currentIsAbsolute, document);
        }

        // Start new section
        currentSectionPath = token.path || '';
        currentIsAbsolute = token.isAbsolute || false;
        sectionStart = i + 1;
      }

      i++;
    }

    // Process final section
    if (sectionStart < tokens.length) {
      const sectionTokens = tokens.slice(sectionStart);
      this.processSection(sectionTokens, currentSectionPath, currentIsAbsolute, document);
    }
  }

  /**
   * Process a section's tokens
   */
  private processSection(
    tokens: Token[],
    sectionPath: string,
    isAbsolute: boolean,
    document: Document
  ): void {
    if (tokens.length === 0) return;

    // Filter out blank lines for analysis
    const contentTokens = tokens.filter(t => t.type !== TokenType.BlankLine);
    if (contentTokens.length === 0) return;

    // Determine section type
    const hasKeyValue = contentTokens.some(
      t => t.type === TokenType.KeyValue || t.type === TokenType.MultilineStart
    );

    if (!hasKeyValue) {
      // Scalar array
      const values = contentTokens
        .filter(t => t.value !== undefined)
        .map(t => this.inferType(t.value!));

      if (isAbsolute) {
        document.set(sectionPath, values);
      } else {
        document.addRelativeSection(sectionPath, values);
      }
    } else {
      // Check for object array (blank line separators)
      if (this.hasBlankLineSeparators(tokens)) {
        const objects = this.parseObjectArray(tokens);
        if (isAbsolute) {
          document.set(sectionPath, objects);
        } else {
          document.addRelativeSection(sectionPath, objects);
        }
      } else {
        // Plain object
        const obj = this.parseObject(tokens);
        if (isAbsolute) {
          for (const [key, value] of Object.entries(obj)) {
            const fullPath = sectionPath ? `${sectionPath}.${key}` : key;
            document.mergeAtPath(fullPath, value);
          }
        } else {
          document.addRelativeSection(sectionPath, obj);
        }
      }
    }
  }

  /**
   * Check if tokens have blank line separators
   */
  private hasBlankLineSeparators(tokens: Token[]): boolean {
    let hasBlank = false;
    let hasContentAfterBlank = false;
    let foundContent = false;

    for (const token of tokens) {
      if (token.type === TokenType.BlankLine) {
        if (foundContent) {
          hasBlank = true;
          foundContent = false;
        }
      } else if (token.type === TokenType.KeyValue || token.type === TokenType.MultilineStart) {
        if (hasBlank) {
          hasContentAfterBlank = true;
        }
        foundContent = true;
      }
    }

    return hasBlank && hasContentAfterBlank;
  }

  /**
   * Parse tokens as an array of objects
   */
  private parseObjectArray(tokens: Token[]): Value[] {
    const objects: { [key: string]: Value }[] = [];
    let currentObject: { [key: string]: Value } = {};

    let i = 0;
    while (i < tokens.length) {
      const token = tokens[i];

      if (token.type === TokenType.BlankLine) {
        if (Object.keys(currentObject).length > 0) {
          objects.push(currentObject);
          currentObject = {};
        }
      } else if (token.type === TokenType.KeyValue) {
        if (token.key && token.value !== undefined) {
          currentObject[token.key] = this.inferType(token.value);
        }
      } else if (token.type === TokenType.MultilineStart) {
        const { value, newIndex } = this.collectMultiline(tokens, i);
        if (token.key) {
          currentObject[token.key] = value;
        }
        i = newIndex;
      }

      i++;
    }

    // Don't forget last object
    if (Object.keys(currentObject).length > 0) {
      objects.push(currentObject);
    }

    return objects;
  }

  /**
   * Parse tokens as a plain object
   */
  private parseObject(tokens: Token[]): { [key: string]: Value } {
    const obj: { [key: string]: Value } = {};

    let i = 0;
    while (i < tokens.length) {
      const token = tokens[i];

      if (token.type === TokenType.KeyValue) {
        if (token.key && token.value !== undefined) {
          this.setNestedValue(obj, token.key, this.inferType(token.value));
        }
      } else if (token.type === TokenType.MultilineStart) {
        const { value, newIndex } = this.collectMultiline(tokens, i);
        if (token.key) {
          this.setNestedValue(obj, token.key, value);
        }
        i = newIndex;
      }

      i++;
    }

    return obj;
  }

  /**
   * Collect multiline value
   */
  private collectMultiline(tokens: Token[], startIdx: number): { value: string; newIndex: number } {
    const parts: string[] = [];

    // Add initial content
    if (tokens[startIdx].value) {
      parts.push(tokens[startIdx].value);
    }

    let i = startIdx + 1;
    while (i < tokens.length) {
      const token = tokens[i];

      if (token.type === TokenType.MultilineContent) {
        if (token.value) {
          parts.push(token.value);
        }
      } else if (token.type === TokenType.MultilineEnd) {
        if (token.value) {
          parts.push(token.value);
        }
        break;
      }

      i++;
    }

    return { value: parts.join('\n'), newIndex: i };
  }

  /**
   * Set nested value in object
   */
  private setNestedValue(obj: { [key: string]: Value }, key: string, value: Value): void {
    if (key.includes('.')) {
      const parts = key.split('.');
      let current: any = obj;

      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        if (!current[part] || typeof current[part] !== 'object' || Array.isArray(current[part])) {
          current[part] = {};
        }
        current = current[part];
      }

      current[parts[parts.length - 1]] = value;
    } else {
      obj[key] = value;
    }
  }

  /**
   * Infer type from string value
   */
  private inferType(value: string): Value {
    if (!this.inferTypes) {
      return value;
    }

    // Try boolean
    const lower = value.toLowerCase();
    if (lower === 'true') return true;
    if (lower === 'false') return false;

    // Try integer
    if (/^-?\d+$/.test(value)) {
      const num = parseInt(value, 10);
      if (!isNaN(num)) return num;
    }

    // Try float
    if (/^-?\d+\.\d+$/.test(value)) {
      const num = parseFloat(value);
      if (!isNaN(num)) return num;
    }

    // Keep as string
    return value;
  }
}

/**
 * Parse ADF text with default options
 */
export function parse(text: string, options?: ParseOptions): Document {
  const parser = new Parser(options);
  return parser.parse(text);
}

/**
 * Parse ADF file (Node.js only)
 */
export function parseFile(path: string, options?: ParseOptions): Document {
  const fs = require('fs');
  const text = fs.readFileSync(path, 'utf-8');
  return parse(text, options);
}
