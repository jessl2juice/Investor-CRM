/**
 * BetterMind CRM - Shared UI Components
 * Reusable Badge, Pill, CopyBtn, InfoRow, and helper functions.
 */
import { useState } from "react";

export const STATUS_COLORS = {
  active:{bg:"#059669",t:"#fff"},diligence:{bg:"#d97706",t:"#fff"},outreach:{bg:"#3b82f6",t:"#fff"},
  follow_up:{bg:"#8b5cf6",t:"#fff"},scheduled:{bg:"#06b6d4",t:"#fff"},passed:{bg:"#6b7280",t:"#fff"},
  connected:{bg:"#10b981",t:"#fff"},recruiting:{bg:"#f59e0b",t:"#000"},searching:{bg:"#ef4444",t:"#fff"},
  contact:{bg:"#94a3b8",t:"#fff"},cold:{bg:"#374151",t:"#fff"},complete:{bg:"#059669",t:"#fff"},
  applied:{bg:"#8b5cf6",t:"#fff"},planning:{bg:"#f59e0b",t:"#000"},
  identified:{bg:"#94a3b8",t:"#fff"},meeting:{bg:"#06b6d4",t:"#fff"},term_sheet:{bg:"#059669",t:"#fff"},
  closed:{bg:"#16a34a",t:"#fff"},dead:{bg:"#374151",t:"#fff"},
};

export const CAT_ICONS = {investor:"💰",google:"🔷",team:"👤",advisor:"🧠",partner:"🤝",vendor:"🔧",university:"🎓",media:"📰",other:"📋"};

export const Badge = ({s}) => {
  const c = STATUS_COLORS[s]||{bg:"#374151",t:"#fff"};
  return <span style={{background:c.bg,color:c.t,padding:"3px 10px",borderRadius:99,fontSize:13,fontWeight:600,letterSpacing:.3,textTransform:"uppercase",whiteSpace:"nowrap"}}>{(s||"").replace(/_/g," ")}</span>;
};

export const Pill = ({children,active,onClick}) => (
  <button type="button" onClick={onClick} style={{
    padding:"8px 16px",borderRadius:99,border:"1px solid",fontSize:14,fontWeight:600,transition:"all .15s",
    background:active?"#1e293b":"transparent",color:active?"#fff":"#64748b",borderColor:active?"#1e293b":"#e2e8f0",
  }}>{children}</button>
);

export const ensureUrl = (url) => url && !url.match(/^https?:\/\//) ? `https://${url}` : url;
export const displayUrl = (url) => url ? url.replace(/^https?:\/\/(www\.)?/, '') : '';

export const formatAddress = (c) => {
  const parts = [c.address_line1, c.address_line2, c.city,
    c.state && c.zip ? `${c.state} ${c.zip}` : (c.state || c.zip),
    c.country && c.country !== 'US' ? c.country : null
  ].filter(Boolean);
  return parts.join(', ');
};

export const CopyBtn = ({value}) => {
  const [ok, setOk] = useState(false);
  const copy = (e) => { e.stopPropagation(); navigator.clipboard.writeText(value).then(()=>{setOk(true);setTimeout(()=>setOk(false),1500);}); };
  return <button onClick={copy} title="Copy" style={{background:"none",border:"1px solid #e2e8f0",borderRadius:6,padding:"2px 8px",fontSize:12,cursor:"pointer",color:ok?"#059669":"#64748b",fontWeight:600,whiteSpace:"nowrap"}}>{ok?"✓ Copied":"Copy"}</button>;
};

export const InfoRow = ({label, value, href, actions}) => {
  if (!value) return null;
  return (
    <div style={{display:"flex",alignItems:"center",gap:8,padding:"7px 0",borderBottom:"1px solid #f1f5f9"}}>
      <div style={{width:80,fontSize:13,fontWeight:600,color:"#94a3b8",flexShrink:0}}>{label}</div>
      <div style={{flex:1,fontSize:15,color:"#0f172a",wordBreak:"break-all"}}>
        {href ? <a href={href} target={href.startsWith("mailto:")||href.startsWith("tel:")?"_self":"_blank"} rel="noopener noreferrer" style={{color:"#2563eb",textDecoration:"none"}} onClick={e=>e.stopPropagation()}>{value}</a> : value}
      </div>
      <div style={{display:"flex",gap:4,flexShrink:0}}>{actions}</div>
    </div>
  );
};
