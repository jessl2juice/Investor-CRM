/**
 * BetterMind CRM - User Management (Admin)
 * CRUD for user accounts, password changes.
 */
import { useState, useEffect, useCallback } from "react";
import { api } from "../api";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("user");
  const [changePw, setChangePw] = useState(null);
  const [changePwVal, setChangePwVal] = useState("");
  const [msg, setMsg] = useState("");
  const [msgIsError, setMsgIsError] = useState(false);

  const loadUsers = useCallback(async () => {
    try { setUsers(await api("/users")); } catch (e) { console.error(e); }
  }, []);
  useEffect(() => { loadUsers(); }, [loadUsers]);

  const addUser = async (e) => {
    e.preventDefault();
    setMsg("");
    try {
      await api("/users", { method: "POST", body: JSON.stringify({ email: newEmail, password: newPassword, name: newName, role: newRole }) });
      setNewEmail(""); setNewName(""); setNewPassword(""); setNewRole("user"); setShowAdd(false);
      loadUsers();
      setMsg("User added"); setMsgIsError(false);
    } catch (err) { setMsg(err.message || "Error adding user"); setMsgIsError(true); }
  };

  const updatePw = async (uid) => {
    setMsg("");
    try {
      await api(`/users/${uid}/password`, { method: "PUT", body: JSON.stringify({ password: changePwVal }) });
      setChangePw(null); setChangePwVal("");
      setMsg("Password updated"); setMsgIsError(false);
    } catch (err) { setMsg(err.message || "Error"); setMsgIsError(true); }
  };

  const deleteUser = async (uid, email) => {
    if (!confirm(`Delete user ${email}?`)) return;
    setMsg("");
    try {
      await api(`/users/${uid}`, { method: "DELETE" });
      loadUsers();
      setMsg("User deleted"); setMsgIsError(false);
    } catch (err) { setMsg(err.message || "Error"); setMsgIsError(true); }
  };

  return (
    <div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
        <h3 style={{fontSize:18,fontWeight:700,margin:0}}>👥 User Management</h3>
        <button onClick={()=>setShowAdd(!showAdd)} style={{padding:"8px 16px",borderRadius:8,border:"none",background:"#1e293b",color:"#fff",fontSize:14,fontWeight:600}}>
          {showAdd ? "Cancel" : "+ Add User"}
        </button>
      </div>
      {msg && <div style={{background:msgIsError?"#fef2f2":"#f0fdf4",color:msgIsError?"#991b1b":"#166534",padding:"8px 14px",borderRadius:8,fontSize:14,marginBottom:12}}>{msg}</div>}

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
