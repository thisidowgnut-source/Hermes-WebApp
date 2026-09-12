const fs = require('fs');
const data = JSON.parse(fs.readFileSync('C:\\Users\\megat\\Hermes-WebApp\\docs\\n8n_async_media_generation.json', 'utf8'));

const waitNode = data.nodes.find(n => n.type === 'n8n-nodes-base.wait');
if (!waitNode || waitNode.parameters.resume !== 'webhook') {
    throw new Error('Wait for Webhook node missing or incorrectly configured');
}
console.log('PASS');
