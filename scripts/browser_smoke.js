async function browserSmoke(page) {
  const username = 'browser' + Date.now();
  await page.goto('http://localhost:3000/register');
  await page.getByRole('textbox', { name: 'Username', exact: true }).fill(username);
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill(username + '@example.com');
  await page.getByRole('textbox', { name: 'Password', exact: true }).fill('BrowserTest2048!');
  await page.getByRole('button', { name: 'Create Account', exact: true }).click();
  await page.waitForURL('**/chat');
  await page.getByRole('link', { name: '📄 Documents' }).click();
  await page.getByLabel('Upload document').setInputFiles('backend/rag/sample_docs/incident_response.md');
  await page.getByRole('status').filter({hasText:'version 1'}).waitFor({timeout:30000});
  await page.getByRole('button', {name:'incident_response.md',exact:true}).click();
  await page.locator('pre').filter({hasText:'Incident Response Runbook'}).waitFor();
  await page.getByRole('link', {name:'💬 Chat'}).click();
  await page.route('**/chat/stream', route => route.fulfill({status:200,contentType:'text/event-stream',body:'data: '+JSON.stringify({type:'token',text:'Verified response'})+'\n\ndata: '+JSON.stringify({type:'response',reply:'Verified response',session_id:'browser',tool_calls:[],tool_traces:[],sources:[],needs_approval:false})+'\n\n'}));
  await page.getByRole('textbox',{name:'Message',exact:true}).fill('Check UI streaming');
  await page.getByRole('button',{name:'Send',exact:true}).click();
  await page.getByText('Verified response',{exact:true}).waitFor();
  await page.getByRole('link', {name:'📄 Documents'}).click();
  await page.getByRole('button',{name:'Delete',exact:true}).click();
}
