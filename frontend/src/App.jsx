/**
 * BetterMind CRM - Main Application
 * Dashboard shell with tabs, search, filters, and data loading.
 */
import { useState, useEffect, useMemo, useCallback } from "react";
import { api, getToken, setToken } from "./api";
import { Badge, Pill, CAT_ICONS, ensureUrl } from "./components/ui";
import LoginScreen from "./components/LoginScreen";
import ContactDetail from "./components/ContactDetail";
import UserManagement from "./components/UserManagement";
import HelpModal from "./components/HelpModal";

const TABS = [
  {key:"all",label:"All",icon:"📋"},{key:"investor",label:"Investors",icon:"💰"},
  {key:"google",label:"Google",icon:"🔷"},{key:"team",label:"Team",icon:"👤"},
  {key:"advisor",label:"Advisors",icon:"🧠"},{key:"pipeline",label:"Pipeline",icon:"📊"},
  {key:"programs",label:"Programs",icon:"🚀"},{key:"settings",label:"Settings",icon:"⚙️",adminOnly:true},
];

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [userRole, setUserRole] = useState(localStorage.getItem("bm_role") || "");
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [contacts, setContacts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showHelp, setShowHelp] = useState(false);

  const logout = () => { setToken(null); localStorage.removeItem("bm_role"); setAuthed(false); };

  const load = useCallback(async () => {
    try {
      const [c, d, p, s] = await Promise.all([
        api("/contacts"), api("/deals"), api("/programs"), api("/stats")
      ]);
      setContacts(c); setDeals(d); setPrograms(p); setStats(s);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { if (authed) load(); }, [authed, load]);

  const filtered = useMemo(() => {
    let list = contacts;
    if (tab !== "all" && tab !== "pipeline" && tab !== "programs") list = list.filter(c => c.category === tab);
    if (statusFilter !== "all") list = list.filter(c => c.status === statusFilter);
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(c => [c.first_name,c.last_name,c.email,c.title,c.notes,c.subcategory,c.organization_name].filter(Boolean).join(" ").toLowerCase().includes(q));
    }
    return list.sort((a,b) => (a.tier||99) - (b.tier||99));
  }, [contacts, tab, search, statusFilter]);

  const statuses = useMemo(() => {
    const s = new Set(); contacts.forEach(c => s.add(c.status));
    return ["all", ...Array.from(s).sort()];
  }, [contacts]);

  if (!authed) return <LoginScreen onLogin={(email, role) => { setUserRole(role || ""); localStorage.setItem("bm_role", role || ""); setAuthed(true); }} />;
  if (loading) return <div style={{display:"flex",justifyContent:"center",alignItems:"center",height:"100vh",fontSize:18,color:"#64748b"}}>🧠 Loading BetterMind CRM...</div>;

  return (
    <div style={{minHeight:"100vh"}}>
      {/* Header */}
      <div style={{background:"linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)",padding:"20px 24px 16px"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14,maxWidth:960,margin:"0 auto 14px"}}>
          <div>
            <h1 style={{margin:0,fontSize:24,fontWeight:700,color:"#f8fafc",letterSpacing:-.3}}>🧠 BetterMind CRM</h1>
            <p style={{margin:"2px 0 0",fontSize:13,color:"#94a3b8"}}>Fundraising · Google · Team · Pipeline</p>
          </div>
          <div style={{display:"flex",gap:16,alignItems:"center"}}>
            {[["📋",stats.total_contacts,"Contacts"],["💰",stats.active_investors,"Active"],["📊",stats.active_deals,"Deals"],["🔗",stats.total_interactions,"Logs"]].map(([icon,val,label])=>(
              <div key={label} style={{textAlign:"center"}}><div style={{fontSize:18,fontWeight:700,color:"#f8fafc"}}>{icon} {val}</div><div style={{fontSize:12,color:"#64748b"}}>{label}</div></div>
            ))}
            <button onClick={()=>setShowHelp(true)} style={{marginLeft:8,padding:"4px 10px",borderRadius:6,border:"1px solid rgba(255,255,255,.2)",background:"transparent",color:"#94a3b8",fontSize:13,fontWeight:600,whiteSpace:"nowrap"}}>❓ Help</button>
            <button onClick={logout} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(255,255,255,.2)",background:"transparent",color:"#94a3b8",fontSize:13,fontWeight:600,whiteSpace:"nowrap"}}>Sign Out</button>
          </div>
        </div>
        <div style={{display:"flex",gap:4,overflowX:"auto",maxWidth:960,margin:"0 auto"}}>
          {TABS.filter(t=>!t.adminOnly||userRole==="admin").map(t=>(
            <button key={t.key} onClick={()=>{setTab(t.key);setStatusFilter("all");}} style={{
              padding:"8px 14px",borderRadius:8,border:"none",fontSize:14,fontWeight:600,whiteSpace:"nowrap",transition:"all .15s",
              background:tab===t.key?"rgba(255,255,255,.15)":"transparent",color:tab===t.key?"#fff":"#94a3b8",
            }}>{t.icon} {t.label}</button>
          ))}
        </div>
      </div>

      <div style={{padding:"14px 20px",maxWidth:960,margin:"0 auto"}}>
        {/* Search + Filters */}
        {tab !== "pipeline" && tab !== "programs" && tab !== "settings" && (
          <div style={{display:"flex",gap:8,marginBottom:14,flexWrap:"wrap"}}>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search contacts, orgs, notes..." style={{flex:1,minWidth:200,padding:"11px 16px",borderRadius:10,border:"1px solid #e2e8f0",fontSize:15,background:"#fff"}} />
            <div style={{display:"flex",gap:3,flexWrap:"wrap"}}>
              {statuses.map(s=><Pill key={s} active={statusFilter===s} onClick={()=>setStatusFilter(s)}>{s==="all"?"All":s.replace(/_/g," ")}</Pill>)}
            </div>
          </div>
        )}

        {/* Pipeline */}
        {tab === "pipeline" && (
          <div>
            <h3 style={{fontSize:18,fontWeight:700,margin:"0 0 10px"}}>💰 Fundraising Pipeline{deals.length>0?` - ${deals.length} Deal${deals.length!==1?"s":""}`:""}</h3>
            {deals.map(d=>(
              <div key={d.id} onClick={()=>d.contact_id&&setSelectedId(d.contact_id)} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:8,cursor:d.contact_id?"pointer":"default",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <div><div style={{fontWeight:700,fontSize:16}}>{d.deal_name}</div><div style={{fontSize:14,color:"#64748b"}}>{d.contact_name}{d.org_name?` · ${d.org_name}`:""}</div></div>
                <div style={{display:"flex",gap:8,alignItems:"center"}}>
                  {d.amount&&<span style={{fontWeight:600,fontSize:15,color:"#059669"}}>{d.amount}</span>}
                  <Badge s={d.stage}/>
                  <div style={{background:`conic-gradient(#3b82f6 ${d.probability*3.6}deg, #e2e8f0 0deg)`,width:32,height:32,borderRadius:99,display:"flex",alignItems:"center",justifyContent:"center"}}>
                    <div style={{background:"#fff",width:24,height:24,borderRadius:99,display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,fontWeight:700}}>{d.probability}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Programs */}
        {tab === "programs" && (
          <div>
            <h3 style={{fontSize:18,fontWeight:700,margin:"0 0 10px"}}>🚀 Programs & Milestones</h3>
            {programs.map(p=>(
              <div key={p.id} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:8}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <div><div style={{fontWeight:700,fontSize:16}}>{p.name}</div><div style={{fontSize:14,color:"#64748b"}}>{p.value||""}{p.start_date?` · Since ${p.start_date}`:""}{p.contact_name?` · ${p.contact_name}`:""}</div>{p.notes&&<div style={{fontSize:14,color:"#475569",marginTop:3}}>{p.notes}</div>}</div>
                  <Badge s={p.status}/>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Settings */}
        {tab === "settings" && <UserManagement />}

        {/* Contact List */}
        {tab !== "pipeline" && tab !== "programs" && tab !== "settings" && (
          <>
            <div style={{fontSize:14,color:"#94a3b8",marginBottom:6,fontWeight:600}}>{filtered.length} contact{filtered.length!==1?"s":""}</div>
            {filtered.map(c=>(
              <div key={c.id} onClick={()=>setSelectedId(c.id)} style={{
                background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"10px 14px",marginBottom:5,cursor:"pointer",
                transition:"all .12s",display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,
              }} onMouseOver={e=>e.currentTarget.style.borderColor="#cbd5e1"} onMouseOut={e=>e.currentTarget.style.borderColor="#e2e8f0"}>
                <div style={{minWidth:0,flex:1}}>
                  <div style={{display:"flex",alignItems:"center",gap:5}}>
                    <span style={{fontSize:15}}>{CAT_ICONS[c.category]||""}</span>
                    <span style={{fontWeight:600,fontSize:15}}>{c.first_name} {c.last_name||""}</span>
                    {c.tier&&<span style={{fontSize:12,color:"#92400e",background:"#fef3c7",padding:"2px 7px",borderRadius:99,fontWeight:700}}>T{c.tier}</span>}
                  </div>
                  <div style={{fontSize:14,color:"#64748b",marginTop:2,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                    {c.title}{c.organization_name?` · ${c.organization_name}`:""}
                  </div>
                </div>
                <div style={{display:"flex",gap:5,alignItems:"center",flexShrink:0}}>
                  <span style={{fontSize:10,lineHeight:1}} title={c.email&&c.phone?"Has email & phone":c.email||c.phone?"Missing email or phone":"Missing email & phone"}>{c.email&&c.phone?"\uD83D\uDFE2":c.email||c.phone?"\uD83D\uDFE1":"\uD83D\uDD34"}</span>
                  {c.email&&<a href={`mailto:${c.email}`} onClick={e=>e.stopPropagation()} title={c.email} style={{fontSize:13,textDecoration:"none"}}>✉️</a>}
                  {c.phone&&<a href={`tel:${c.phone}`} onClick={e=>e.stopPropagation()} title={c.phone} style={{fontSize:13,textDecoration:"none"}}>📞</a>}
                  {c.linkedin_url&&<a href={ensureUrl(c.linkedin_url)} target="_blank" rel="noopener noreferrer" onClick={e=>e.stopPropagation()} title="LinkedIn" style={{fontSize:13,textDecoration:"none"}}>🔗</a>}
                  <Badge s={c.status}/>
                  {c.last_contact_date&&<span style={{fontSize:13,color:"#94a3b8",whiteSpace:"nowrap"}}>{c.last_contact_date}</span>}
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {selectedId && <ContactDetail id={selectedId} onClose={()=>setSelectedId(null)} onRefresh={load} />}
      {showHelp && <HelpModal onClose={()=>setShowHelp(false)} />}
    </div>
  );
}
