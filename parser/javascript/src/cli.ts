#!/usr/bin/env node

import * as fs from 'fs';
import * as path from 'path';
import { parseFile } from './parser';

function main() {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    printUsage();
    process.exit(1);
  }

  const command = args[0];

  try {
    switch (command) {
      case 'parse':
      case 'check':
        if (args.length < 2) {
          console.error('Error: Missing file path');
          printUsage();
          process.exit(1);
        }
        checkFile(args[1]);
        break;

      case 'to-json':
        if (args.length < 2) {
          console.error('Error: Missing file path');
          printUsage();
          process.exit(1);
        }
        toJson(args[1]);
        break;

      case '--help':
      case '-h':
        printHelp();
        break;

      case '--version':
      case '-v':
        const pkg = require('../package.json');
        console.log(`adf-parser ${pkg.version}`);
        break;

      default:
        console.error(`Error: Unknown command '${command}'`);
        printUsage();
        process.exit(1);
    }
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Error: ${error.message}`);
    } else {
      console.error('Error:', error);
    }
    process.exit(1);
  }
}

function checkFile(filePath: string) {
  const doc = parseFile(filePath);
  const obj = doc.toObject();
  const keys = Object.keys(obj);

  console.log('✓ Valid ADF document');
  console.log(`  ${keys.length} keys in root`);
}

function toJson(filePath: string) {
  const doc = parseFile(filePath);
  const json = doc.toJSON();
  console.log(json);
}

function printUsage() {
  console.log('Usage: adf <command> [args]');
  console.log();
  console.log('Commands:');
  console.log('  parse <file>     Parse and validate an ADF file');
  console.log('  check <file>     Alias for parse');
  console.log('  to-json <file>   Convert ADF to JSON');
  console.log('  --help, -h       Show this help message');
  console.log('  --version, -v    Show version');
}

function printHelp() {
  console.log('ADF Parser - TypeScript/JavaScript implementation');
  console.log();
  printUsage();
  console.log();
  console.log('Examples:');
  console.log('  adf parse config.adf');
  console.log('  adf to-json config.adf > config.json');
  console.log();
  console.log('For more information, visit: https://github.com/Solifugus/ADF');
}

main();
