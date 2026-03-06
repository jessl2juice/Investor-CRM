/**
 * BetterMind CRM - Login Screen
 */
import { useState } from "react";
import { setToken } from "../api";

const API = "/api";

export default function LoginScreen({ onLogin }) {
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
