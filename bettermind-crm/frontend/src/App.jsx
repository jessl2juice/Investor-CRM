import { useState, useEffect, useMemo, useCallback } from "react";

const API = "/api";

function getToken() { return localStorage.getItem("bm_token"); }
function setToken(t) { if (t) localStorage.setItem("bm_token", t); else localStorage.removeItem("bm_token"); }

async function api(path, opts) {
  const token = getToken();
  const r = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    ...opts,
  });
  if (r.status === 401) { setToken(null); window.location.reload(); throw new Error("Unauthorized"); }
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const r = await fetch(`${API}/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!r.ok) { setError("Invalid email or password"); setLoading(false); return; }
      const data = await r.json();
      setToken(data.token);
      onLogin(data.email);
    } catch { setError("Connection error"); setLoading(false); }
  };

  return (
    <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:"linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)"}}>
      <form onSubmit={handleSubmit} style={{background:"#fff",borderRadius:16,padding:36,width:"90%",maxWidth:380,boxShadow:"0 25px 50px rgba(0,0,0,.3)"}}>
        <div style={{textAlign:"center",marginBottom:24}}>
          <div style={{fontSize:32,marginBottom:4}}>🧠</div>
          <h1 style={{margin:0,fontSize:22,fontWeight:700,color:"#0f172a"}}>BetterMind CRM</h1>
          <p style={{margin:"4px 0 0",fontSize:13,color:"#64748b"}}>Sign in to continue</p>
        </div>
        {error && <div style={{background:"#fef2f2",color:"#dc2626",padding:"8px 12px",borderRadius:8,fontSize:13,marginBottom:12,textAlign:"center"}}>{error}</div>}
        <div style={{marginBottom:12}}>
          <label style={{display:"block",fontSize:12,fontWeight:600,color:"#374151",marginBottom:4}}>Email</label>
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required autoFocus
            style={{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:14,boxSizing:"border-box"}} />
        </div>
        <div style={{marginBottom:20}}>
          <label style={{display:"block",fontSize:12,fontWeight:600,color:"#374151",marginBottom:4}}>Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required
            style={{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:14,boxSizing:"border-box"}} />
        </div>
        <button type="submit" disabled={loading} style={{width:"100%",padding:"11px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:14,fontWeight:600,opacity:loading?.6:1}}>
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </div>
  );
}

const STATUS_COLORS = {
  active:{bg:"#059669",t:"#fff"},diligence:{bg:"#d97706",t:"#fff"},outreach:{bg:"#3b82f6",t:"#fff"},
  follow_up:{bg:"#8b5cf6",t:"#fff"},scheduled:{bg:"#06b6d4",t:"#fff"},passed:{bg:"#6b7280",t:"#fff"},
  connected:{bg:"#10b981",t:"#fff"},recruiting:{bg:"#f59e0b",t:"#000"},searching:{bg:"#ef4444",t:"#fff"},
  contact:{bg:"#94a3b8",t:"#fff"},cold:{bg:"#374151",t:"#fff"},complete:{bg:"#059669",t:"#fff"},
  applied:{bg:"#8b5cf6",t:"#fff"},planning:{bg:"#f59e0b",t:"#000"},
  identified:{bg:"#94a3b8",t:"#fff"},meeting:{bg:"#06b6d4",t:"#fff"},term_sheet:{bg:"#059669",t:"#fff"},
  closed:{bg:"#16a34a",t:"#fff"},dead:{bg:"#374151",t:"#fff"},
};
const CAT_ICONS = {investor:"💰",google:"🔷",team:"👤",advisor:"🧠",partner:"🤝",vendor:"🔧",university:"🎓",media:"📰",other:"📋"};

const Badge = ({s}) => {
  const c = STATUS_COLORS[s]||{bg:"#374151",t:"#fff"};
  return <span style={{background:c.bg,color:c.t,padding:"2px 8px",borderRadius:99,fontSize:11,fontWeight:600,letterSpacing:.3,textTransform:"uppercase",whiteSpace:"nowrap"}}>{(s||"").replace(/_/g," ")}</span>;
};

const Pill = ({children,active,onClick}) => (
  <button onClick={onClick} style={{
    padding:"6px 14px",borderRadius:99,border:"1px solid",fontSize:12,fontWeight:600,transition:"all .15s",
    background:active?"#1e293b":"transparent",color:active?"#fff":"#64748b",borderColor:active?"#1e293b":"#e2e8f0",
  }}>{children}</button>
);

function ContactDetail({id, onClose}) {
  const [c, setC] = useState(null);
  const [newNote, setNewNote] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { api(`/contacts/${id}`).then(setC); }, [id]);

  const logInteraction = async () => {
    if (!newNote.trim()) return;
    setSaving(true);
    await api("/interactions", {
      method: "POST",
      body: JSON.stringify({
        contact_id: id, type: "note", channel: "other",
        subject: "Manual note", summary: newNote,
        date: new Date().toISOString().split("T")[0],
      }),
    });
    setNewNote("");
    const updated = await api(`/contacts/${id}`);
    setC(updated);
    setSaving(false);
  };

  if (!c) return <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",display:"flex",justifyContent:"center",alignItems:"center",zIndex:999}}><div style={{color:"#fff",fontSize:16}}>Loading...</div></div>;

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",display:"flex",justifyContent:"center",alignItems:"flex-start",paddingTop:48,zIndex:999,overflowY:"auto"}} onClick={onClose}>
      <div style={{background:"#fff",borderRadius:16,width:"92%",maxWidth:660,margin:"0 auto 48px",padding:28,boxShadow:"0 25px 50px rgba(0,0,0,.2)"}} onClick={e=>e.stopPropagation()}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:20}}>
          <div>
            <h2 style={{margin:0,fontSize:22,fontWeight:700,color:"#0f172a"}}>{CAT_ICONS[c.category]} {c.first_name} {c.last_name||""}</h2>
            <p style={{margin:"4px 0 0",color:"#64748b",fontSize:14}}>{c.title}{c.organization_name?` · ${c.organization_name}`:""}</p>
          </div>
          <div style={{display:"flex",gap:8,alignItems:"center"}}>
            <Badge s={c.status}/>
            {c.tier && <span style={{background:"#fef3c7",color:"#92400e",padding:"2px 8px",borderRadius:99,fontSize:11,fontWeight:700}}>T{c.tier}</span>}
            <button onClick={onClose} style={{background:"none",border:"none",fontSize:20,cursor:"pointer",color:"#94a3b8"}}>✕</button>
          </div>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:18}}>
          {c.email && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:10,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>Email</div><div style={{fontSize:13,color:"#0f172a",wordBreak:"break-all"}}>{c.email}</div></div>}
          {c.phone && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:10,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>Phone</div><div style={{fontSize:13,color:"#0f172a"}}>{c.phone}</div></div>}
          {c.linkedin_url && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:10,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>LinkedIn</div><a href={`https://${c.linkedin_url}`} target="_blank" rel="noopener noreferrer" style={{fontSize:13,color:"#2563eb"}}>{c.linkedin_url}</a></div>}
          {c.last_contact_date && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:10,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>Last Contact</div><div style={{fontSize:13}}>{c.last_contact_date}</div></div>}
        </div>

        {c.next_action && <div style={{background:"#eff6ff",borderRadius:8,padding:12,marginBottom:14,borderLeft:"3px solid #3b82f6"}}><div style={{fontSize:10,color:"#3b82f6",fontWeight:700,textTransform:"uppercase"}}>Next Action{c.next_action_date?` · ${c.next_action_date}`:""}</div><div style={{fontSize:13,color:"#1e40af",marginTop:2}}>{c.next_action}</div></div>}
        {c.notes && <div style={{background:"#f8fafc",borderRadius:8,padding:12,marginBottom:14}}><div style={{fontSize:10,color:"#94a3b8",fontWeight:600,textTransform:"uppercase",marginBottom:4}}>Notes</div><div style={{fontSize:13,color:"#334155",lineHeight:1.5}}>{c.notes}</div></div>}

        {c.deals?.length > 0 && <div style={{marginBottom:14}}><div style={{fontSize:12,fontWeight:700,textTransform:"uppercase",marginBottom:6}}>Pipeline</div>{c.deals.map((d,i)=><div key={i} style={{background:"#fefce8",borderRadius:8,padding:10,marginBottom:4,display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><span style={{fontWeight:600,fontSize:13}}>{d.deal_name}</span>{d.amount&&<span style={{color:"#64748b",fontSize:12,marginLeft:8}}>{d.amount}</span>}</div><div style={{display:"flex",gap:6}}><Badge s={d.stage}/><span style={{fontSize:11,color:"#94a3b8"}}>{d.probability}%</span></div></div>)}</div>}

        {c.interactions?.length > 0 && <div style={{marginBottom:14}}><div style={{fontSize:12,fontWeight:700,textTransform:"uppercase",marginBottom:6}}>Activity Log</div>{c.interactions.map((int,i)=><div key={i} style={{display:"flex",gap:10,marginBottom:6,paddingBottom:6,borderBottom:"1px solid #f1f5f9"}}><div style={{fontSize:11,color:"#94a3b8",whiteSpace:"nowrap",minWidth:72}}>{int.date}</div><div><span style={{fontSize:11,color:"#3b82f6",fontWeight:600}}>{int.type.replace(/_/g," ")}</span>{int.subject&&<span style={{fontSize:11,color:"#94a3b8"}}> — {int.subject}</span>}<div style={{fontSize:12,color:"#475569",marginTop:1}}>{int.summary}</div></div></div>)}</div>}

        <div style={{borderTop:"1px solid #e2e8f0",paddingTop:12,display:"flex",gap:8}}>
          <input value={newNote} onChange={e=>setNewNote(e.target.value)} placeholder="Add a note or log activity..." style={{flex:1,padding:"8px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:13}} onKeyDown={e=>{if(e.key==="Enter")logInteraction()}}/>
          <button onClick={logInteraction} disabled={saving} style={{padding:"8px 16px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:12,fontWeight:600,opacity:saving?.5:1}}>
            {saving?"Saving...":"Log"}
          </button>
        </div>
      </div>
    </div>
  );
}

const TABS = [
  {key:"all",label:"All",icon:"📋"},{key:"investor",label:"Investors",icon:"💰"},
  {key:"google",label:"Google",icon:"🔷"},{key:"team",label:"Team",icon:"👤"},
  {key:"advisor",label:"Advisors",icon:"🧠"},{key:"pipeline",label:"Pipeline",icon:"📊"},
  {key:"programs",label:"Programs",icon:"🚀"},
];

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [contacts, setContacts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = () => { setToken(null); setAuthed(false); };

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

  if (!authed) return <LoginScreen onLogin={() => setAuthed(true)} />;
  if (loading) return <div style={{display:"flex",justifyContent:"center",alignItems:"center",height:"100vh",fontSize:18,color:"#64748b"}}>🧠 Loading BetterMind CRM...</div>;

  return (
    <div style={{minHeight:"100vh"}}>
      {/* Header */}
      <div style={{background:"linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)",padding:"20px 24px 16px"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14,maxWidth:960,margin:"0 auto 14px"}}>
          <div>
            <h1 style={{margin:0,fontSize:20,fontWeight:700,color:"#f8fafc",letterSpacing:-.3}}>🧠 BetterMind CRM</h1>
            <p style={{margin:"2px 0 0",fontSize:11,color:"#94a3b8"}}>Fundraising · Google · Team · Pipeline</p>
          </div>
          <div style={{display:"flex",gap:16,alignItems:"center"}}>
            {[["📋",stats.total_contacts,"Contacts"],["💰",stats.active_investors,"Active"],["📊",stats.active_deals,"Deals"],["🔗",stats.total_interactions,"Logs"]].map(([icon,val,label],i)=>(
              <div key={i} style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:700,color:"#f8fafc"}}>{icon} {val}</div><div style={{fontSize:9,color:"#64748b"}}>{label}</div></div>
            ))}
            <button onClick={logout} style={{marginLeft:8,padding:"4px 10px",borderRadius:6,border:"1px solid rgba(255,255,255,.2)",background:"transparent",color:"#94a3b8",fontSize:11,fontWeight:600,whiteSpace:"nowrap"}}>Sign Out</button>
          </div>
        </div>
        <div style={{display:"flex",gap:4,overflowX:"auto",maxWidth:960,margin:"0 auto"}}>
          {TABS.map(t=>(
            <button key={t.key} onClick={()=>{setTab(t.key);setStatusFilter("all");}} style={{
              padding:"6px 12px",borderRadius:8,border:"none",fontSize:12,fontWeight:600,whiteSpace:"nowrap",transition:"all .15s",
              background:tab===t.key?"rgba(255,255,255,.15)":"transparent",color:tab===t.key?"#fff":"#94a3b8",
            }}>{t.icon} {t.label}</button>
          ))}
        </div>
      </div>

      <div style={{padding:"14px 20px",maxWidth:960,margin:"0 auto"}}>
        {/* Search + Filters */}
        {tab !== "pipeline" && tab !== "programs" && (
          <div style={{display:"flex",gap:8,marginBottom:14,flexWrap:"wrap"}}>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search contacts, orgs, notes..." style={{flex:1,minWidth:200,padding:"9px 14px",borderRadius:10,border:"1px solid #e2e8f0",fontSize:13,background:"#fff"}} />
            <div style={{display:"flex",gap:3,flexWrap:"wrap"}}>
              {statuses.map(s=><Pill key={s} active={statusFilter===s} onClick={()=>setStatusFilter(s)}>{s==="all"?"All":s.replace(/_/g," ")}</Pill>)}
            </div>
          </div>
        )}

        {/* Pipeline */}
        {tab === "pipeline" && (
          <div>
            <h3 style={{fontSize:15,fontWeight:700,margin:"0 0 10px"}}>💰 Fundraising Pipeline — $2.5M Seed</h3>
            {deals.map((d,i)=>(
              <div key={i} onClick={()=>d.contact_id&&setSelectedId(d.contact_id)} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:8,cursor:d.contact_id?"pointer":"default",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <div><div style={{fontWeight:700,fontSize:14}}>{d.deal_name}</div><div style={{fontSize:12,color:"#64748b"}}>{d.contact_name}{d.org_name?` · ${d.org_name}`:""}</div></div>
                <div style={{display:"flex",gap:8,alignItems:"center"}}>
                  {d.amount&&<span style={{fontWeight:600,fontSize:13,color:"#059669"}}>{d.amount}</span>}
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
            <h3 style={{fontSize:15,fontWeight:700,margin:"0 0 10px"}}>🚀 Programs & Milestones</h3>
            {programs.map((p,i)=>(
              <div key={i} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:8}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <div><div style={{fontWeight:700,fontSize:14}}>{p.name}</div><div style={{fontSize:12,color:"#64748b"}}>{p.value||""}{p.start_date?` · Since ${p.start_date}`:""}{p.contact_name?` · ${p.contact_name}`:""}</div>{p.notes&&<div style={{fontSize:12,color:"#475569",marginTop:3}}>{p.notes}</div>}</div>
                  <Badge s={p.status}/>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Contact List */}
        {tab !== "pipeline" && tab !== "programs" && (
          <>
            <div style={{fontSize:12,color:"#94a3b8",marginBottom:6,fontWeight:600}}>{filtered.length} contact{filtered.length!==1?"s":""}</div>
            {filtered.map(c=>(
              <div key={c.id} onClick={()=>setSelectedId(c.id)} style={{
                background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"10px 14px",marginBottom:5,cursor:"pointer",
                transition:"all .12s",display:"flex",justifyContent:"space-between",alignItems:"center",gap:10,
              }} onMouseOver={e=>e.currentTarget.style.borderColor="#cbd5e1"} onMouseOut={e=>e.currentTarget.style.borderColor="#e2e8f0"}>
                <div style={{minWidth:0,flex:1}}>
                  <div style={{display:"flex",alignItems:"center",gap:5}}>
                    <span style={{fontSize:12}}>{CAT_ICONS[c.category]||""}</span>
                    <span style={{fontWeight:600,fontSize:13}}>{c.first_name} {c.last_name||""}</span>
                    {c.tier&&<span style={{fontSize:9,color:"#92400e",background:"#fef3c7",padding:"1px 5px",borderRadius:99,fontWeight:700}}>T{c.tier}</span>}
                  </div>
                  <div style={{fontSize:11,color:"#64748b",marginTop:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                    {c.title}{c.organization_name?` · ${c.organization_name}`:""}
                  </div>
                </div>
                <div style={{display:"flex",gap:5,alignItems:"center",flexShrink:0}}>
                  {c.email&&<span style={{fontSize:9}}>✉️</span>}
                  {c.phone&&<span style={{fontSize:9}}>📞</span>}
                  <Badge s={c.status}/>
                  {c.last_contact_date&&<span style={{fontSize:10,color:"#94a3b8",whiteSpace:"nowrap"}}>{c.last_contact_date}</span>}
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {selectedId && <ContactDetail id={selectedId} onClose={()=>{setSelectedId(null);load();}} />}
    </div>
  );
}
