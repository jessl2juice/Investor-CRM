/**
 * BetterMind CRM - Contact Detail Modal
 * Displays full contact info with edit mode, delete, interaction logging.
 */
import { useState, useEffect, useCallback } from "react";
import { api } from "../api";
import { Badge, CAT_ICONS, CopyBtn, InfoRow, ensureUrl, displayUrl, formatAddress } from "./ui";

export default function ContactDetail({id, onClose, onRefresh}) {
  const [c, setC] = useState(null);
  const [newNote, setNewNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [deleting, setDeleting] = useState(false);

  const reload = useCallback(() => api(`/contacts/${id}`).then(setC).catch(console.error), [id]);
  useEffect(() => { reload(); }, [reload]);

  const logInteraction = async () => {
    if (!newNote.trim()) return;
    setSaving(true);
    try {
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
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
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
    try {
      const payload = {};
      Object.entries(editData).forEach(([k, v]) => { payload[k] = v.trim() || null; });
      await api(`/contacts/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      await reload();
      setEditing(false);
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete ${c.first_name} ${c.last_name || ""}? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await api(`/contacts/${id}`, { method: "DELETE" });
      onClose();
      if (onRefresh) onRefresh();
    } catch (e) { console.error(e); setDeleting(false); }
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
            {c.deals.map(d=><div key={d.id} style={{background:"#fefce8",borderRadius:8,padding:10,marginBottom:4,display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><span style={{fontWeight:600,fontSize:15}}>{d.deal_name}</span>{d.amount&&<span style={{color:"#64748b",fontSize:14,marginLeft:8}}>{d.amount}</span>}</div><div style={{display:"flex",gap:6}}><Badge s={d.stage}/><span style={{fontSize:13,color:"#94a3b8"}}>{d.probability}%</span></div></div>)}
          </div>
        )}

        {/* INTERACTIONS */}
        {c.interactions?.length > 0 && (
          <div style={{marginBottom:16}}>
            <div style={{fontSize:13,fontWeight:700,textTransform:"uppercase",color:"#64748b",marginBottom:6}}>Activity Log</div>
            {c.interactions.map(ix=><div key={ix.id} style={{display:"flex",gap:10,marginBottom:6,paddingBottom:6,borderBottom:"1px solid #f1f5f9"}}><div style={{fontSize:13,color:"#94a3b8",whiteSpace:"nowrap",minWidth:72}}>{ix.date}</div><div><span style={{fontSize:13,color:"#3b82f6",fontWeight:600}}>{ix.type.replace(/_/g," ")}</span>{ix.subject&&<span style={{fontSize:13,color:"#94a3b8"}}> — {ix.subject}</span>}<div style={{fontSize:14,color:"#475569",marginTop:1}}>{ix.summary}</div></div></div>)}
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
