/**
 * Represents a value in an ADF document
 */
export type Value = string | number | boolean | null | Value[] | { [key: string]: Value };

/**
 * Parse options
 */
export interface ParseOptions {
  /** Whether to infer types (int, float, bool) from strings */
  inferTypes?: boolean;
  /** Strict mode (throw on errors) vs lenient mode (skip errors) */
  strict?: boolean;
}

/**
 * Token types for lexer
 */
export enum TokenType {
  BlankLine = 'blank',
  AbsoluteHeader = 'absolute_header',
  RelativeHeader = 'relative_header',
  KeyValue = 'key_value',
  ScalarValue = 'scalar_value',
  MultilineStart = 'multiline_start',
  MultilineContent = 'multiline_content',
  MultilineEnd = 'multiline_end',
}

/**
 * Token from lexer
 */
export interface Token {
  type: TokenType;
  lineNumber: number;
  rawLine: string;
  path?: string;
  isAbsolute?: boolean;
  key?: string;
  value?: string;
  constraint?: string;
  quoteCount?: number;
}

/**
 * ADF parsing error
 */
export class AdfError extends Error {
  constructor(
    message: string,
    public lineNumber?: number,
    public context?: string
  ) {
    super(lineNumber !== undefined ? `Line ${lineNumber}: ${message}` : message);
    this.name = 'AdfError';
  }
}
