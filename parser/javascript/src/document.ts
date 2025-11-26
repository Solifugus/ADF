import { Value } from './types';

/**
 * Represents a parsed ADF document
 */
export class Document {
  private root: { [key: string]: Value } = {};
  private relativeSections: { [key: string]: Value } = {};

  /**
   * Get a value by dot-notation path
   */
  get(path: string, defaultValue?: Value): Value | undefined {
    if (!path) {
      return this.root;
    }

    const parts = this.parsePath(path);
    let current: any = this.root;

    for (const part of parts) {
      if (current && typeof current === 'object' && !Array.isArray(current)) {
        current = current[part];
      } else {
        return defaultValue;
      }
    }

    return current !== undefined ? current : defaultValue;
  }

  /**
   * Set a value by dot-notation path
   */
  set(path: string, value: Value): void {
    if (!path) {
      if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
        this.root = value;
      }
      return;
    }

    const parts = this.parsePath(path);
    let current: any = this.root;

    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current[part] || typeof current[part] !== 'object' || Array.isArray(current[part])) {
        current[part] = {};
      }
      current = current[part];
    }

    current[parts[parts.length - 1]] = value;
  }

  /**
   * Merge another document into this one
   */
  merge(other: Document): void {
    this.root = this.deepMerge(this.root, other.root);
  }

  /**
   * Merge data at a specific path
   */
  mergeAtPath(path: string, value: Value): void {
    const existing = this.get(path);

    if (existing && typeof existing === 'object' && !Array.isArray(existing) &&
        typeof value === 'object' && !Array.isArray(value)) {
      const merged = this.deepMerge(existing, value);
      this.set(path, merged);
    } else {
      this.set(path, value);
    }
  }

  /**
   * Get relative sections
   */
  getRelativeSections(): { [key: string]: Value } {
    return { ...this.relativeSections };
  }

  /**
   * Add a relative section
   */
  addRelativeSection(path: string, value: Value): void {
    const parts = this.parsePath(path);
    let current: any = this.relativeSections;

    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current[part]) {
        current[part] = {};
      }
      current = current[part];
    }

    current[parts[parts.length - 1]] = value;
  }

  /**
   * Convert to plain object
   */
  toObject(): { [key: string]: Value } {
    return JSON.parse(JSON.stringify(this.root));
  }

  /**
   * Convert to JSON string
   */
  toJSON(indent: number = 2): string {
    return JSON.stringify(this.root, null, indent);
  }

  /**
   * Parse a dot-notation path into parts
   */
  private parsePath(path: string): string[] {
    const parts: string[] = [];
    let current = '';
    let inQuotes = false;

    for (const char of path) {
      if (char === '"') {
        inQuotes = !inQuotes;
        current += char;
      } else if (char === '.' && !inQuotes) {
        if (current) {
          parts.push(this.unquoteKey(current));
          current = '';
        }
      } else {
        current += char;
      }
    }

    if (current) {
      parts.push(this.unquoteKey(current));
    }

    return parts;
  }

  /**
   * Remove quotes from a quoted key
   */
  private unquoteKey(key: string): string {
    if (key.startsWith('"') && key.endsWith('"') && key.length >= 2) {
      return key.slice(1, -1);
    }
    return key;
  }

  /**
   * Deep merge two objects
   */
  private deepMerge(base: any, overlay: any): any {
    if (typeof base !== 'object' || Array.isArray(base) ||
        typeof overlay !== 'object' || Array.isArray(overlay)) {
      return overlay;
    }

    const result = { ...base };

    for (const [key, value] of Object.entries(overlay)) {
      if (key in result && typeof result[key] === 'object' && !Array.isArray(result[key]) &&
          typeof value === 'object' && !Array.isArray(value)) {
        result[key] = this.deepMerge(result[key], value);
      } else {
        result[key] = value;
      }
    }

    return result;
  }
}
