const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const root=__dirname;
const validation=JSON.parse(fs.readFileSync(path.join(root,'parts/validation.json'),'utf8'));
const index=Object.fromEntries(validation.map(x=>[x.name,x]));
const labels={
head:'Head + front hair',ponytail:'High ponytail + bow',torso:'Clothed torso + front skirt',
arm_viewer_left:'Arm - image left',arm_viewer_right:'Arm - image right',skirt_back:'Rear skirt - ORIGINAL PURPLE',
sleeve_tail_viewer_right:'Sleeve tail - belongs to RIGHT ARM',leg_viewer_left:'Booted leg - image left',
leg_viewer_right:'Booted leg - image right',tassel:'Red waist knot + tassel'};
const order=['head','ponytail','torso','arm_viewer_left','arm_viewer_right','skirt_back','sleeve_tail_viewer_right','leg_viewer_left','leg_viewer_right','tassel'];
const items=order.map(id=>({label:labels[id],file:'parts/'+id+'.png',bbox:index[id].bbox}));
items.push({label:'Slender sword - chibi',file:'weapons/sword_slender_chibi.png',bbox:[378,53,646,1471]});
items.push({label:'Wide ice sword - chibi',file:'weapons/sword_ice_chibi.png',bbox:[241,31,784,1506]});
const W=1280,CW=320,CH=360,TOP=78,H=TOP+3*CH+35;
let svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'"><defs><pattern id="check" width="24" height="24" patternUnits="userSpaceOnUse"><rect width="24" height="24" fill="#f4f6fb"/><rect width="12" height="12" fill="#dce2ec"/><rect x="12" y="12" width="12" height="12" fill="#dce2ec"/></pattern></defs><rect width="100%" height="100%" fill="#e9edf5"/><text x="22" y="34" font-size="24" font-family="Arial" font-weight="700" fill="#22324b">JINGLIU - CUTOUT PARTS / ALPHA REVIEW</text><text x="22" y="59" font-size="15" font-family="Arial" fill="#4d5d75">10 character layers + 2 props | original purple retained | moon ribbon belongs to the arm sleeve</text>';
for (let i=0;i<items.length;i++){
 const x=(i%4)*CW,y=TOP+Math.floor(i/4)*CH,it=items[i],b=it.bbox;
 const s=Math.min((CW-38)/(b[2]-b[0]),(CH-65)/(b[3]-b[1]));
 const tx=x+(CW-(b[2]-b[0])*s)/2-b[0]*s;
 const ty=y+45+(CH-65-(b[3]-b[1])*s)/2-b[1]*s;
 const data=fs.readFileSync(path.join(root,it.file)).toString('base64');
 svg+='<rect x="'+(x+8)+'" y="'+(y+6)+'" width="'+(CW-16)+'" height="'+(CH-12)+'" rx="8" fill="url(#check)" stroke="#c3ccdb"/><rect x="'+(x+8)+'" y="'+(y+6)+'" width="'+(CW-16)+'" height="34" rx="7" fill="#fff"/><text x="'+(x+18)+'" y="'+(y+29)+'" font-size="14" font-family="Arial" fill="#20354f">'+(i+1)+'. '+it.label+'</text><g transform="translate('+tx+' '+ty+') scale('+s+')"><image href="data:image/png;base64,'+data+'" width="1024" height="1536"/></g>';
}
svg+='<text x="22" y="'+(H-12)+'" font-size="13" font-family="Arial" fill="#50617a">Static inspection only. Extracted pieces still require rig alignment before animation.</text></svg>';
fs.writeFileSync(path.join(root,'parts_overview.svg'),svg);
sharp(Buffer.from(svg)).png().toFile(path.join(root,'parts_overview.png')).then(()=>console.log('Created parts_overview.png')).catch(e=>{console.error(e);process.exit(1)});

