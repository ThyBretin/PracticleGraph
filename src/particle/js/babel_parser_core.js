const { parse } = require('@babel/parser');
const fs = require('fs');
const path = require('path');

function parseFile(filePath) {
  try {
    const absolutePath = filePath.startsWith('/project/') ? filePath : path.join('/project', filePath);
    console.error(`Reading file from: ${absolutePath}`);
    const code = fs.readFileSync(absolutePath, 'utf-8');

    // TypeScript heuristic
    const hasTypeScriptSyntax =
      code.includes(': ') ||
      code.includes('<T>') ||
      code.includes('interface ') ||
      code.includes('type ') ||
      absolutePath.endsWith('.ts') ||
      absolutePath.endsWith('.tsx');

    const plugins = ['jsx', 'decorators-legacy'];
    if (hasTypeScriptSyntax) {
      plugins.push('typescript');
    } else {
      plugins.push('flow');
    }

    const ast = parse(code, {
      sourceType: 'module',
      plugins,
      tokens: true,
      comments: true,
    });

    return { ast, code }; // Return code for existing Particle merge later
  } catch (error) {
    console.error(`Error parsing ${filePath}: ${error.message}`);
    throw error; // Let caller handle
  }
}

if (require.main === module) {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('No file path provided');
    process.exit(1);
  }
  const { ast, code } = parseFile(filePath);
  console.log(JSON.stringify({ ast, code }));
}

module.exports = { parseFile };