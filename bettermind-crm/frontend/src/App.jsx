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

const ensureUrl = (url) => url && !url.match(/^https?:\/\//) ? `https://${url}` : url;
const displayUrl = (url) => url ? url.replace(/^https?:\/\/(www\.)?/, '') : '';
const formatAddress = (c) => {
  const parts = [c.address_line1, c.address_line2, c.city,
    c.state && c.zip ? `${c.state} ${c.zip}` : (c.state || c.zip),
    c.country && c.country !== 'US' ? c.country : null
  ].filter(Boolean);
  return parts.join(', ');
};

const CopyBtn = ({value}) => {
  const [ok, setOk] = useState(false);
  const copy = (e) => { e.stopPropagation(); navigator.clipboard.writeText(value).then(()=>{setOk(true);setTimeout(()=>setOk(false),1500);}); };
  return <button onClick={copy} title="Copy" style={{background:"none",border:"1px solid #e2e8f0",borderRadius:6,padding:"2px 8px",fontSize:12,cursor:"pointer",color:ok?"#059669":"#64748b",fontWeight:600,whiteSpace:"nowrap"}}>{ok?"✓ Copied":"Copy"}</button>;
};

const InfoRow = ({label, value, href, actions}) => {
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

function ContactDetail({id, onClose, onRefresh}) {
  const [c, setC] = useState(null);
  const [newNote, setNewNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [deleting, setDeleting] = useState(false);

  const reload = () => api(`/contacts/${id}`).then(setC);
  useEffect(() => { reload(); }, [id]);

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
    await reload();
    setSaving(false);
  };

  const startEdit = () => {
    setEditData({
      email: c.email || "", email_secondary: c.email_secondary || "",
      phone: c.phone || "", phone_secondary: c.phone_secondary || "",
      linkedin_url: c.linkedin_url || "", website: c.website || "", twitter_url: c.twitter_url || "",
      address_line1: c.address_line1 || "", address_line2: c.address_line2 || "",
      city: c.city || "", state: c.state || "", zip: c.zip || "", country: c.country || "US",
    });
    setEditing(true);
  };

  const saveEdit = async () => {
    setSaving(true);
    const payload = {};
    Object.entries(editData).forEach(([k, v]) => { payload[k] = v.trim() || null; });
    await api(`/contacts/${id}`, { method: "PUT", body: JSON.stringify(payload) });
    await reload();
    setEditing(false);
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!confirm(`Delete ${c.first_name} ${c.last_name || ""}? This cannot be undone.`)) return;
    setDeleting(true);
    await api(`/contacts/${id}`, { method: "DELETE" });
    onClose();
    if (onRefresh) onRefresh();
  };

  const ef = (field) => ({ value: editData[field], onChange: e => setEditData({...editData, [field]: e.target.value}) });
  const inputStyle = {width:"100%",padding:"8px 10px",borderRadius:6,border:"1px solid #e2e8f0",fontSize:14,boxSizing:"border-box"};

  if (!c) return <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",display:"flex",justifyContent:"center",alignItems:"center",zIndex:999}}><div style={{color:"#fff",fontSize:16}}>Loading...</div></div>;

  const addr = formatAddress(c);
  const hasAnyContact = c.email || c.email_secondary || c.phone || c.phone_secondary || c.linkedin_url || c.website || c.twitter_url || addr;

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",display:"flex",justifyContent:"center",alignItems:"flex-start",paddingTop:48,zIndex:999,overflowY:"auto"}} onClick={onClose}>
      <div style={{background:"#fff",borderRadius:16,width:"92%",maxWidth:700,margin:"0 auto 48px",padding:28,boxShadow:"0 25px 50px rgba(0,0,0,.2)"}} onClick={e=>e.stopPropagation()}>

        {/* HEADER */}
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:20}}>
          <div>
            <h2 style={{margin:0,fontSize:24,fontWeight:700,color:"#0f172a"}}>{CAT_ICONS[c.category]} {c.first_name} {c.last_name||""}</h2>
            <p style={{margin:"4px 0 0",color:"#64748b",fontSize:16}}>{c.title}{c.organization_name?` at ${c.organization_name}`:""}</p>
          </div>
          <div style={{display:"flex",gap:6,alignItems:"center",flexShrink:0}}>
            <Badge s={c.status}/>
            {c.tier && <span style={{background:"#fef3c7",color:"#92400e",padding:"3px 10px",borderRadius:99,fontSize:13,fontWeight:700}}>T{c.tier}</span>}
            <span style={{fontSize:12,color:"#94a3b8",background:"#f1f5f9",padding:"3px 10px",borderRadius:99,fontWeight:600}}>{c.category}</span>
            {!editing && <button onClick={startEdit} style={{padding:"5px 12px",borderRadius:6,border:"1px solid #e2e8f0",background:"#fff",fontSize:13,fontWeight:600,color:"#374151",cursor:"pointer"}}>Edit</button>}
            <button onClick={handleDelete} disabled={deleting} style={{padding:"5px 12px",borderRadius:6,border:"1px solid #fecaca",background:"#fff",fontSize:13,fontWeight:600,color:"#dc2626",cursor:"pointer",opacity:deleting?.5:1}}>{deleting?"...":"Delete"}</button>
            <button onClick={onClose} style={{background:"none",border:"none",fontSize:20,cursor:"pointer",color:"#94a3b8"}}>✕</button>
          </div>
        </div>

        {/* CONTACT INFORMATION CARD */}
        <div style={{border:"1px solid #e2e8f0",borderRadius:12,padding:"12px 16px",marginBottom:16,background:"#fafbfc"}}>
          <div style={{fontSize:13,fontWeight:700,textTransform:"uppercase",color:"#64748b",marginBottom:6}}>Contact Information</div>
          {editing ? (
            <div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:10}}>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Email</label><input type="email" {...ef("email")} placeholder="email@example.com" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Email (Secondary)</label><input type="email" {...ef("email_secondary")} placeholder="secondary@example.com" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Phone</label><input type="tel" {...ef("phone")} placeholder="(555) 555-5555" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Phone (Secondary)</label><input type="tel" {...ef("phone_secondary")} placeholder="(555) 555-5555" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>LinkedIn URL</label><input type="url" {...ef("linkedin_url")} placeholder="linkedin.com/in/username" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Website</label><input type="url" {...ef("website")} placeholder="https://example.com" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Twitter/X</label><input type="url" {...ef("twitter_url")} placeholder="twitter.com/username" style={inputStyle}/></div>
              </div>
              <div style={{fontSize:13,fontWeight:700,color:"#64748b",marginBottom:6}}>Address</div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:10}}>
                <div style={{gridColumn:"1/-1"}}><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Address Line 1</label><input {...ef("address_line1")} placeholder="Street address" style={inputStyle}/></div>
                <div style={{gridColumn:"1/-1"}}><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Address Line 2</label><input {...ef("address_line2")} placeholder="Suite, apt, unit" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>City</label><input {...ef("city")} placeholder="City" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>State</label><input {...ef("state")} placeholder="State" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Zip</label><input {...ef("zip")} placeholder="Zip/Postal code" style={inputStyle}/></div>
                <div><label style={{fontSize:12,fontWeight:600,color:"#374151"}}>Country</label><input {...ef("country")} placeholder="Country" style={inputStyle}/></div>
              </div>
              <div style={{display:"flex",gap:8,justifyContent:"flex-end"}}>
                <button onClick={()=>setEditing(false)} style={{padding:"8px 16px",borderRadius:8,border:"1px solid #e2e8f0",background:"#fff",fontSize:14,fontWeight:600,color:"#374151",cursor:"pointer"}}>Cancel</button>
                <button onClick={saveEdit} disabled={saving} style={{padding:"8px 16px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:14,fontWeight:600,cursor:"pointer",opacity:saving?.6:1}}>{saving?"Saving...":"Save"}</button>
              </div>
            </div>
          ) : hasAnyContact ? (
            <div>
              <InfoRow label="Email" value={c.email} href={`mailto:${c.email}`} actions={<CopyBtn value={c.email}/>}/>
              <InfoRow label="Email 2" value={c.email_secondary} href={`mailto:${c.email_secondary}`} actions={<CopyBtn value={c.email_secondary}/>}/>
              <InfoRow label="Phone" value={c.phone} href={`tel:${c.phone}`} actions={<CopyBtn value={c.phone}/>}/>
              <InfoRow label="Phone 2" value={c.phone_secondary} href={`tel:${c.phone_secondary}`} actions={<CopyBtn value={c.phone_secondary}/>}/>
              <InfoRow label="LinkedIn" value={c.linkedin_url ? displayUrl(c.linkedin_url) : null} href={ensureUrl(c.linkedin_url)}/>
              <InfoRow label="Website" value={c.website ? displayUrl(c.website) : null} href={ensureUrl(c.website)}/>
              <InfoRow label="Twitter/X" value={c.twitter_url ? displayUrl(c.twitter_url) : null} href={ensureUrl(c.twitter_url)}/>
              <InfoRow label="Address" value={addr || null} href={addr ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}` : null}/>
            </div>
          ) : (
            <div style={{color:"#94a3b8",fontSize:14,fontStyle:"italic",padding:"8px 0"}}>No contact information. Click Edit to add.</div>
          )}
        </div>

        {/* PIPELINE & ACTIONS */}
        {(c.last_contact_date || c.next_action) && (
          <div style={{border:"1px solid #e2e8f0",borderRadius:12,padding:"12px 16px",marginBottom:16,background:"#fafbfc"}}>
            <div style={{fontSize:13,fontWeight:700,textTransform:"uppercase",color:"#64748b",marginBottom:6}}>Pipeline & Actions</div>
            {c.last_contact_date && <div style={{fontSize:14,color:"#475569",marginBottom:4}}><span style={{fontWeight:600}}>Last Contact:</span> {c.last_contact_date}</div>}
            {c.next_action && <div style={{background:"#eff6ff",borderRadius:8,padding:10,borderLeft:"3px solid #3b82f6",marginTop:6}}><div style={{fontSize:12,color:"#3b82f6",fontWeight:700,textTransform:"uppercase"}}>Next Action{c.next_action_date?` · ${c.next_action_date}`:""}</div><div style={{fontSize:15,color:"#1e40af",marginTop:2}}>{c.next_action}</div></div>}
          </div>
        )}

        {/* NOTES */}
        {c.notes && (
          <div style={{border:"1px solid #e2e8f0",borderRadius:12,padding:"12px 16px",marginBottom:16,background:"#fafbfc"}}>
            <div style={{fontSize:13,fontWeight:700,textTransform:"uppercase",color:"#64748b",marginBottom:6}}>Notes</div>
            <div style={{fontSize:15,color:"#334155",lineHeight:1.5}}>{c.notes}</div>
          </div>
        )}

        {/* DEALS */}
        {c.deals?.length > 0 && (
          <div style={{marginBottom:16}}>
            <div style={{fontSize:13,fontWeight:700,textTransform:"uppercase",color:"#64748b",marginBottom:6}}>Deals</div>
            {c.deals.map((d,i)=><div key={i} style={{background:"#fefce8",borderRadius:8,padding:10,marginBottom:4,display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><span style={{fontWeight:600,fontSize:15}}>{d.deal_name}</span>{d.amount&&<span style={{color:"#64748b",fontSize:14,marginLeft:8}}>{d.amount}</span>}</div><div style={{display:"flex",gap:6}}><Badge s={d.stage}/><span style={{fontSize:13,color:"#94a3b8"}}>{d.probability}%</span></div></div>)}
          </div>
        )}

        {/* INTERACTIONS */}
        {c.interactions?.length > 0 && (
          <div style={{marginBottom:16}}>
            <div style={{fontSize:13,fontWeight:700,textTransform:"uppercase",color:"#64748b",marginBottom:6}}>Activity Log</div>
            {c.interactions.map((int,i)=><div key={i} style={{display:"flex",gap:10,marginBottom:6,paddingBottom:6,borderBottom:"1px solid #f1f5f9"}}><div style={{fontSize:13,color:"#94a3b8",whiteSpace:"nowrap",minWidth:72}}>{int.date}</div><div><span style={{fontSize:13,color:"#3b82f6",fontWeight:600}}>{int.type.replace(/_/g," ")}</span>{int.subject&&<span style={{fontSize:13,color:"#94a3b8"}}> — {int.subject}</span>}<div style={{fontSize:14,color:"#475569",marginTop:1}}>{int.summary}</div></div></div>)}
          </div>
        )}

        {/* LOG NOTE */}
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

function HelpModal({onClose}) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/help").then(d => { setContent(d.content); setLoading(false); }).catch(() => { setContent("Failed to load help content."); setLoading(false); });
  }, []);

  const renderMarkdown = (md) => {
    const lines = md.split("\n");
    const html = [];
    let inCode = false, codeLang = "", codeLines = [];
    let inTable = false, tableRows = [];

    const flush = () => {
      if (inCode) {
        html.push(`<pre style="background:#1e293b;color:#e2e8f0;padding:14px 16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.5;margin:8px 0"><code>${codeLines.join("\n").replace(/</g,"&lt;").replace(/>/g,"&gt;")}</code></pre>`);
        codeLines = []; inCode = false;
      }
      if (inTable && tableRows.length) {
        const headerCells = tableRows[0].split("|").filter(c=>c.trim());
        let t = '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:14px"><thead><tr>';
        headerCells.forEach(c => t += `<th style="text-align:left;padding:6px 10px;border-bottom:2px solid #e2e8f0;font-weight:600;color:#374151">${c.trim()}</th>`);
        t += '</tr></thead><tbody>';
        for (let i = 2; i < tableRows.length; i++) {
          const cells = tableRows[i].split("|").filter(c=>c.trim());
          t += '<tr>';
          cells.forEach(c => t += `<td style="padding:6px 10px;border-bottom:1px solid #f1f5f9;color:#475569">${inline(c.trim())}</td>`);
          t += '</tr>';
        }
        t += '</tbody></table>';
        html.push(t);
        tableRows = []; inTable = false;
      }
    };

    const inline = (text) => {
      return text
        .replace(/</g,"&lt;").replace(/>/g,"&gt;")
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:13px;color:#dc2626">$1</code>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:#2563eb">$1</a>');
    };

    for (const line of lines) {
      if (line.startsWith("```")) {
        if (inCode) { flush(); } else { flush(); inCode = true; codeLang = line.slice(3).trim(); }
        continue;
      }
      if (inCode) { codeLines.push(line); continue; }

      if (line.includes("|") && line.trim().startsWith("|")) {
        if (!inTable) { flush(); inTable = true; }
        tableRows.push(line);
        continue;
      } else if (inTable) { flush(); }

      if (line.startsWith("# ")) { flush(); html.push(`<h1 style="font-size:24px;font-weight:700;margin:24px 0 8px;color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:8px">${inline(line.slice(2))}</h1>`); }
      else if (line.startsWith("## ")) { flush(); html.push(`<h2 style="font-size:20px;font-weight:700;margin:20px 0 6px;color:#0f172a">${inline(line.slice(3))}</h2>`); }
      else if (line.startsWith("### ")) { flush(); html.push(`<h3 style="font-size:17px;font-weight:700;margin:16px 0 4px;color:#1e293b">${inline(line.slice(4))}</h3>`); }
      else if (line.startsWith("---")) { html.push('<hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0"/>'); }
      else if (line.match(/^\d+\.\s/)) { html.push(`<div style="margin:2px 0 2px 20px;font-size:15px;color:#334155">${inline(line.replace(/^\d+\.\s/, '<span style="color:#64748b;font-weight:600;margin-right:4px">$&</span>'))}</div>`); }
      else if (line.match(/^\s*-\s/)) {
        const indent = line.match(/^(\s*)/)[1].length;
        html.push(`<div style="margin:2px 0 2px ${16 + indent * 8}px;font-size:15px;color:#334155">• ${inline(line.replace(/^\s*-\s/, ''))}</div>`);
      }
      else if (line.trim()) { html.push(`<p style="margin:4px 0;font-size:15px;line-height:1.6;color:#334155">${inline(line)}</p>`); }
    }
    flush();
    return html.join("");
  };

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.5)",display:"flex",justifyContent:"center",alignItems:"flex-start",paddingTop:32,zIndex:1000,overflowY:"auto"}} onClick={onClose}>
      <div style={{background:"#fff",borderRadius:16,width:"94%",maxWidth:800,margin:"0 auto 48px",boxShadow:"0 25px 50px rgba(0,0,0,.2)",display:"flex",flexDirection:"column",maxHeight:"90vh"}} onClick={e=>e.stopPropagation()}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"16px 24px",borderBottom:"1px solid #e2e8f0",flexShrink:0}}>
          <h2 style={{margin:0,fontSize:20,fontWeight:700,color:"#0f172a"}}>📖 User Manual</h2>
          <button onClick={onClose} style={{background:"none",border:"none",fontSize:20,cursor:"pointer",color:"#94a3b8"}}>✕</button>
        </div>
        <div style={{padding:"16px 24px",overflowY:"auto",flex:1}}>
          {loading ? <div style={{textAlign:"center",padding:40,color:"#64748b"}}>Loading...</div>
            : <div dangerouslySetInnerHTML={{__html: renderMarkdown(content)}} />}
        </div>
      </div>
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
            {[["📋",stats.total_contacts,"Contacts"],["💰",stats.active_investors,"Active"],["📊",stats.active_deals,"Deals"],["🔗",stats.total_interactions,"Logs"]].map(([icon,val,label],i)=>(
              <div key={i} style={{textAlign:"center"}}><div style={{fontSize:18,fontWeight:700,color:"#f8fafc"}}>{icon} {val}</div><div style={{fontSize:12,color:"#64748b"}}>{label}</div></div>
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
