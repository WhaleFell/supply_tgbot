import{d as g,o as h,r as x,l as C,m as E,w as a,n as T,e as V,a as e,b as k,t as m,f as v,p as B,q as y,s as $,i as N,k as U,v as z}from"./index-1ddb36b3.js";/* empty css                 */import{s as d}from"./apis-1181872a.js";const D={style:{"margin-left":"10px"}},A=g({__name:"Users",setup(I){const r=()=>{d.get("/user/get_all_user").then(o=>c.value=o.data).catch(function(o){console.log(o)})},i=(o,u)=>{d.post("/user/set_user_amount/",{user_id:o,amount:u}).then(n=>{let l=n.data;B.alert(`当前${l.username}(${l.user_id})余额:${l.amount}`,"用户金额修改成功!",{confirmButtonText:"OK"}),r()}).catch(function(n){console.log(n)})};h(()=>{r()});const c=x([]);return(o,u)=>{const n=C("timer"),l=y,s=$,p=N,f=U,b=z,w=T;return V(),E(w,null,{default:a(()=>[e(b,{data:c.value,style:{width:"100%"}},{default:a(()=>[e(s,{label:"用户信息"},{default:a(t=>[e(l,null,{default:a(()=>[e(n)]),_:1}),k("span",D,m(t.row.username)+"("+m(t.row.user_id)+")",1)]),_:1}),e(s,{label:"余额"},{default:a(t=>[e(p,{modelValue:t.row.amount,"onUpdate:modelValue":_=>t.row.amount=_},null,8,["modelValue","onUpdate:modelValue"]),e(f,{type:"primary",onClick:_=>i(t.row.user_id,t.row.amount)},{default:a(()=>[v(" 修改 ")]),_:2},1032,["onClick"])]),_:1}),e(s,{prop:"count",label:"发布次数"}),e(s,{prop:"create_at",label:"注册时间"})]),_:1},8,["data"])]),_:1})}}});export{A as default};