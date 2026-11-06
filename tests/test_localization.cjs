// Tests pure display translation without a browser or a provider request.
const fs=require('node:fs');const assert=require('node:assert/strict');
const path=require('node:path');const root=path.resolve(__dirname,'..');
const locales=JSON.parse(fs.readFileSync(path.join(root,'public/locales.json'),'utf8'));
const app=fs.readFileSync(path.join(root,'public/app.js'),'utf8');
const source=app.slice(app.indexOf('function translateText('),app.indexOf('const originalUiText='));
for(const language of Object.keys(locales)){
 const translate=Function('locales','language',source+';return translateText;')(locales,language);
 assert.equal(translate('GST certificate'),locales[language].ui['GST certificate']);
 assert.equal(translate('Valid until 2027-01-31'),locales[language].ui['Valid until {date}'].replace('{date}','2027-01-31'));
 assert.equal(translate(' ₹2,124 '),' ₹2,124 ');
 assert.equal(translate('P09'),'P09');
 assert.equal(translate('UDYAM-AS-00-1234567'),'UDYAM-AS-00-1234567');
 assert.equal(translate('Aether'),'Aether');
 for(const key of ['Purpose: check business registration, address and signatory details for this bundle.','I agree to local processing for the purpose above.','Check documents','Create demo order','Order received','Services activated'])assert.ok(locales[language].ui[key],language+': '+key);
}
console.log('Locale display tests passed for '+Object.keys(locales).length+' non-English languages.');
