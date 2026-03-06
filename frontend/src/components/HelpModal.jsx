/**
 * BetterMind CRM - Help Modal
 * Fetches and renders the user manual as formatted HTML.
 */
import { useState, useEffect } from "react";
import { api } from "../api";

export default function HelpModal({onClose}) {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/help").then(d => { setContent(d.content); setLoading(false); }).catch(() => { setContent("Failed to load help content."); setLoading(false); });
  }, []);

  const renderMarkdown = (md) => {
    const lines = md.split("\n");
    const html = [];
    let inCode = false, codeLines = [];
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
        if (inCode) { flush(); } else { flush(); inCode = true; }
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
        html.push(`<div style="margin:2px 0 2px ${16 + indent * 8}px;font-size:15px;color:#334155">${"\u2022"} ${inline(line.replace(/^\s*-\s/, ''))}</div>`);
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
