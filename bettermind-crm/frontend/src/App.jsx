import { useState, useEffect, useMemo, useCallback } from "react";

const API = "/api";

function getToken() { return localStorage.getItem("bm_token"); }
function setToken(t) { if (t) localStorage.setItem("bm_token", t); else localStorage.removeItem("bm_token"); }

async function api(path, opts = {}) {
  const token = getToken();
  const { headers: customHeaders, ...restOpts } = opts;
  const r = await fetch(`${API}${path}`, {
    ...restOpts,
    headers: { "Content-Type": "application/json", ...customHeaders, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
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
      setLoading(false);
      onLogin(data.email, data.role);
    } catch { setError("Connection error"); setLoading(false); }
  };

  return (
    <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:"linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)"}}>
      <form onSubmit={handleSubmit} style={{background:"#fff",borderRadius:16,padding:36,width:"90%",maxWidth:380,boxShadow:"0 25px 50px rgba(0,0,0,.3)"}}>
        <div style={{textAlign:"center",marginBottom:24}}>
          <div style={{fontSize:32,marginBottom:4}}>🧠</div>
          <h1 style={{margin:0,fontSize:26,fontWeight:700,color:"#0f172a"}}>BetterMind CRM</h1>
          <p style={{margin:"4px 0 0",fontSize:15,color:"#64748b"}}>Sign in to continue</p>
        </div>
        {error && <div style={{background:"#fef2f2",color:"#dc2626",padding:"8px 12px",borderRadius:8,fontSize:15,marginBottom:12,textAlign:"center"}}>{error}</div>}
        <div style={{marginBottom:12}}>
          <label style={{display:"block",fontSize:14,fontWeight:600,color:"#374151",marginBottom:4}}>Email</label>
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required autoFocus
            style={{width:"100%",padding:"12px 14px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:16,boxSizing:"border-box"}} />
        </div>
        <div style={{marginBottom:20}}>
          <label style={{display:"block",fontSize:14,fontWeight:600,color:"#374151",marginBottom:4}}>Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} required
            style={{width:"100%",padding:"12px 14px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:16,boxSizing:"border-box"}} />
        </div>
        <button type="submit" disabled={loading} style={{width:"100%",padding:"13px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:16,fontWeight:600,opacity:loading?.6:1}}>
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
  return <span style={{background:c.bg,color:c.t,padding:"3px 10px",borderRadius:99,fontSize:13,fontWeight:600,letterSpacing:.3,textTransform:"uppercase",whiteSpace:"nowrap"}}>{(s||"").replace(/_/g," ")}</span>;
};

const Pill = ({children,active,onClick}) => (
  <button onClick={onClick} style={{
    padding:"8px 16px",borderRadius:99,border:"1px solid",fontSize:14,fontWeight:600,transition:"all .15s",
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
            <h2 style={{margin:0,fontSize:24,fontWeight:700,color:"#0f172a"}}>{CAT_ICONS[c.category]} {c.first_name} {c.last_name||""}</h2>
            <p style={{margin:"4px 0 0",color:"#64748b",fontSize:16}}>{c.title}{c.organization_name?` · ${c.organization_name}`:""}</p>
          </div>
          <div style={{display:"flex",gap:8,alignItems:"center"}}>
            <Badge s={c.status}/>
            {c.tier && <span style={{background:"#fef3c7",color:"#92400e",padding:"3px 10px",borderRadius:99,fontSize:13,fontWeight:700}}>T{c.tier}</span>}
            <button onClick={onClose} style={{background:"none",border:"none",fontSize:20,cursor:"pointer",color:"#94a3b8"}}>✕</button>
          </div>
        </div>

        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:18}}>
          {c.email && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:12,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>Email</div><div style={{fontSize:15,color:"#0f172a",wordBreak:"break-all"}}>{c.email}</div></div>}
          {c.phone && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:12,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>Phone</div><div style={{fontSize:15,color:"#0f172a"}}>{c.phone}</div></div>}
          {c.linkedin_url && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:12,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>LinkedIn</div><a href={c.linkedin_url.startsWith("http")?c.linkedin_url:`https://${c.linkedin_url}`} target="_blank" rel="noopener noreferrer" style={{fontSize:15,color:"#2563eb"}}>{c.linkedin_url}</a></div>}
          {c.last_contact_date && <div style={{background:"#f8fafc",borderRadius:8,padding:10}}><div style={{fontSize:12,color:"#94a3b8",fontWeight:600,textTransform:"uppercase"}}>Last Contact</div><div style={{fontSize:15}}>{c.last_contact_date}</div></div>}
        </div>

        {c.next_action && <div style={{background:"#eff6ff",borderRadius:8,padding:12,marginBottom:14,borderLeft:"3px solid #3b82f6"}}><div style={{fontSize:12,color:"#3b82f6",fontWeight:700,textTransform:"uppercase"}}>Next Action{c.next_action_date?` · ${c.next_action_date}`:""}</div><div style={{fontSize:15,color:"#1e40af",marginTop:2}}>{c.next_action}</div></div>}
        {c.notes && <div style={{background:"#f8fafc",borderRadius:8,padding:12,marginBottom:14}}><div style={{fontSize:12,color:"#94a3b8",fontWeight:600,textTransform:"uppercase",marginBottom:4}}>Notes</div><div style={{fontSize:15,color:"#334155",lineHeight:1.5}}>{c.notes}</div></div>}

        {c.deals?.length > 0 && <div style={{marginBottom:14}}><div style={{fontSize:14,fontWeight:700,textTransform:"uppercase",marginBottom:6}}>Pipeline</div>{c.deals.map((d,i)=><div key={i} style={{background:"#fefce8",borderRadius:8,padding:10,marginBottom:4,display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><span style={{fontWeight:600,fontSize:15}}>{d.deal_name}</span>{d.amount&&<span style={{color:"#64748b",fontSize:14,marginLeft:8}}>{d.amount}</span>}</div><div style={{display:"flex",gap:6}}><Badge s={d.stage}/><span style={{fontSize:13,color:"#94a3b8"}}>{d.probability}%</span></div></div>)}</div>}

        {c.interactions?.length > 0 && <div style={{marginBottom:14}}><div style={{fontSize:14,fontWeight:700,textTransform:"uppercase",marginBottom:6}}>Activity Log</div>{c.interactions.map((int,i)=><div key={i} style={{display:"flex",gap:10,marginBottom:6,paddingBottom:6,borderBottom:"1px solid #f1f5f9"}}><div style={{fontSize:13,color:"#94a3b8",whiteSpace:"nowrap",minWidth:72}}>{int.date}</div><div><span style={{fontSize:13,color:"#3b82f6",fontWeight:600}}>{int.type.replace(/_/g," ")}</span>{int.subject&&<span style={{fontSize:13,color:"#94a3b8"}}> — {int.subject}</span>}<div style={{fontSize:14,color:"#475569",marginTop:1}}>{int.summary}</div></div></div>)}</div>}

        <div style={{borderTop:"1px solid #e2e8f0",paddingTop:12,display:"flex",gap:8}}>
          <input value={newNote} onChange={e=>setNewNote(e.target.value)} placeholder="Add a note or log activity..." style={{flex:1,padding:"10px 14px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:15}} onKeyDown={e=>{if(e.key==="Enter")logInteraction()}}/>
          <button onClick={logInteraction} disabled={saving} style={{padding:"10px 18px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:14,fontWeight:600,opacity:saving?.5:1}}>
            {saving?"Saving...":"Log"}
          </button>
        </div>
      </div>
    </div>
  );
}

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("user");
  const [changePw, setChangePw] = useState(null);
  const [changePwVal, setChangePwVal] = useState("");
  const [msg, setMsg] = useState("");

  const loadUsers = async () => {
    try { setUsers(await api("/users")); } catch (e) { console.error(e); }
  };
  useEffect(() => { loadUsers(); }, []);

  const addUser = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      await api("/users", { method: "POST", body: JSON.stringify({ email: newEmail, password: newPassword, name: newName, role: newRole }) });
      setNewEmail(""); setNewName(""); setNewPassword(""); setNewRole("user"); setShowAdd(false);
      loadUsers();
      setMsg("User added");
    } catch (err) { setMsg(err.message || "Error adding user"); }
  };

  const updatePw = async (uid) => {
    setMsg("");
    try {
      await api(`/users/${uid}/password`, { method: "PUT", body: JSON.stringify({ password: changePwVal }) });
      setChangePw(null); setChangePwVal("");
      setMsg("Password updated");
    } catch (err) { setMsg(err.message || "Error"); }
  };

  const deleteUser = async (uid, email) => {
    if (!confirm(`Delete user ${email}?`)) return;
    setMsg("");
    try {
      await api(`/users/${uid}`, { method: "DELETE" });
      loadUsers();
      setMsg("User deleted");
    } catch (err) { setMsg(err.message || "Error"); }
  };

  return (
    <div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
        <h3 style={{fontSize:18,fontWeight:700,margin:0}}>👥 User Management</h3>
        <button onClick={()=>setShowAdd(!showAdd)} style={{padding:"8px 16px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:14,fontWeight:600}}>
          {showAdd ? "Cancel" : "+ Add User"}
        </button>
      </div>
      {msg && <div style={{background:"#f0fdf4",color:"#166534",padding:"8px 14px",borderRadius:8,fontSize:14,marginBottom:12}}>{msg}</div>}

      {showAdd && (
        <form onSubmit={addUser} style={{background:"#f8fafc",borderRadius:10,padding:16,marginBottom:14,border:"1px solid #e2e8f0"}}>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:10}}>
            <div>
              <label style={{display:"block",fontSize:13,fontWeight:600,color:"#374151",marginBottom:3}}>Email</label>
              <input type="email" value={newEmail} onChange={e=>setNewEmail(e.target.value)} required
                style={{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:15,boxSizing:"border-box"}} />
            </div>
            <div>
              <label style={{display:"block",fontSize:13,fontWeight:600,color:"#374151",marginBottom:3}}>Name</label>
              <input value={newName} onChange={e=>setNewName(e.target.value)}
                style={{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:15,boxSizing:"border-box"}} />
            </div>
            <div>
              <label style={{display:"block",fontSize:13,fontWeight:600,color:"#374151",marginBottom:3}}>Password</label>
              <input type="password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} required
                style={{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:15,boxSizing:"border-box"}} />
            </div>
            <div>
              <label style={{display:"block",fontSize:13,fontWeight:600,color:"#374151",marginBottom:3}}>Role</label>
              <select value={newRole} onChange={e=>setNewRole(e.target.value)}
                style={{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:15,boxSizing:"border-box",background:"#fff"}}>
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <button type="submit" style={{padding:"10px 20px",borderRadius:8,border:"none",background:"#059669",color:"#fff",fontSize:14,fontWeight:600}}>Create User</button>
        </form>
      )}

      {users.map(u=>(
        <div key={u.id} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:6}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <div>
              <div style={{fontWeight:600,fontSize:15}}>{u.name || u.email}</div>
              <div style={{fontSize:14,color:"#64748b"}}>{u.email}</div>
            </div>
            <div style={{display:"flex",gap:8,alignItems:"center"}}>
              <span style={{background:u.role==="admin"?"#7c3aed":"#3b82f6",color:"#fff",padding:"3px 10px",borderRadius:99,fontSize:13,fontWeight:600,textTransform:"uppercase"}}>{u.role}</span>
              <button onClick={()=>{setChangePw(changePw===u.id?null:u.id);setChangePwVal("");}} style={{padding:"6px 12px",borderRadius:6,border:"1px solid #e2e8f0",background:"#fff",fontSize:13,fontWeight:600,color:"#374151"}}>Password</button>
              <button onClick={()=>deleteUser(u.id,u.email)} style={{padding:"6px 12px",borderRadius:6,border:"1px solid #fecaca",background:"#fff",fontSize:13,fontWeight:600,color:"#dc2626"}}>Delete</button>
            </div>
          </div>
          {changePw===u.id && (
            <div style={{display:"flex",gap:8,marginTop:10}}>
              <input type="password" value={changePwVal} onChange={e=>setChangePwVal(e.target.value)} placeholder="New password"
                style={{flex:1,padding:"10px 12px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:15}} />
              <button onClick={()=>updatePw(u.id)} disabled={!changePwVal}
                style={{padding:"10px 16px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:14,fontWeight:600,opacity:changePwVal?1:.5}}>Update</button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

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
            {[["📋",stats.total_contacts,"Contacts"],["💰",stats.active_investors,"Active"],["📊",stats.active_deals,"Deals"],["🔗",stats.total_interactions,"Logs"]].map(([icon,val,label],i)=>(
              <div key={i} style={{textAlign:"center"}}><div style={{fontSize:18,fontWeight:700,color:"#f8fafc"}}>{icon} {val}</div><div style={{fontSize:12,color:"#64748b"}}>{label}</div></div>
            ))}
            <button onClick={logout} style={{marginLeft:8,padding:"4px 10px",borderRadius:6,border:"1px solid rgba(255,255,255,.2)",background:"transparent",color:"#94a3b8",fontSize:13,fontWeight:600,whiteSpace:"nowrap"}}>Sign Out</button>
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
        {tab !== "pipeline" && tab !== "programs" && (
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
            <h3 style={{fontSize:18,fontWeight:700,margin:"0 0 10px"}}>💰 Fundraising Pipeline{deals.length>0?` — ${deals.length} Deal${deals.length!==1?"s":""}`:""}</h3>
            {deals.map((d,i)=>(
              <div key={i} onClick={()=>d.contact_id&&setSelectedId(d.contact_id)} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:8,cursor:d.contact_id?"pointer":"default",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
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
            {programs.map((p,i)=>(
              <div key={i} style={{background:"#fff",borderRadius:10,border:"1px solid #e2e8f0",padding:"12px 16px",marginBottom:8}}>
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
                  {c.email&&<span style={{fontSize:13}}>✉️</span>}
                  {c.phone&&<span style={{fontSize:13}}>📞</span>}
                  <Badge s={c.status}/>
                  {c.last_contact_date&&<span style={{fontSize:13,color:"#94a3b8",whiteSpace:"nowrap"}}>{c.last_contact_date}</span>}
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
