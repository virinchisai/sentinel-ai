async function browserSmokeFinish(page) {
  await page.getByRole('button',{name:'incident_response.md',exact:true}).waitFor({state:'hidden'});
  await page.getByRole('button',{name:'Log out',exact:true}).click();
  await page.waitForURL('**/login');
}
