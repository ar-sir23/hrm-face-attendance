import Compliance from "./pages/Compliance";
import Production from "./pages/Production";
import AntiSpoof from "./pages/AntiSpoof";
import Leaves from "./pages/Leaves";
import Shifts from "./pages/Shifts";
import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Camera    from "./pages/Camera";
import Employees from "./pages/Employees";
import Reports   from "./pages/Reports";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("dashboard");

  const nav = [
    { id:"dashboard", label:"Dashboard",   icon:"📊" },
    { id:"camera",    label:"Live Camera", icon:"📷" },
    { id:"employees", label:"Employees",   icon:"👥" },
    { id:"reports",   label:"Reports",     icon:"📋" },
    { id:"shifts", label:"Shifts", icon:"🕐" },
    { id:"production", label:"Production", icon:"🏭" },
    { id:"leaves", label:"Leaves", icon:"🏖" },
    { id:"antispoof", label:"Anti-Spoof", icon:"🛡️" },
    { id:"compliance", label:"Compliance", icon:"📜" },
  ];

  return (
    <div style={S.layout}>
      <aside style={S.sidebar}>
        <div style={S.logo}>
          <div style={S.logoIcon}>👁</div>
          <div>
            <div style={S.logoText}>FaceHRM</div>
            <div style={S.logoSub}>Attendance System</div>
          </div>
        </div>
        <nav style={S.nav}>
          {nav.map(n => (
            <button key={n.id} style={{...S.navItem, ...(page===n.id?S.navActive:{})}} onClick={()=>setPage(n.id)}>
              <span>{n.icon}</span><span>{n.label}</span>
            </button>
          ))}
        </nav>
        <div style={S.footer}>
          <div style={S.userBox}>
            <div style={S.avatar}>AD</div>
            <div>
              <div style={{fontSize:13,fontWeight:600}}>Admin</div>
              <div style={{fontSize:11,color:"#8b949e"}}>Super Admin</div>
            </div>
          </div>
        </div>
      </aside>

      <main style={S.main}>
        <div style={S.topbar}>
          <span style={{fontSize:18,fontWeight:700}}>
            {nav.find(n=>n.id===page)?.icon} {nav.find(n=>n.id===page)?.label}
          </span>
          <div style={S.badge}>
            <div style={S.dot}/>
            System Active
          </div>
        </div>
        <div style={S.content}>
          {page==="dashboard" && <Dashboard/>}
          {page==="camera"    && <Camera/>}
          {page==="employees" && <Employees/>}
          {page==="reports"   && <Reports/>}
          {page==="shifts" && <Shifts/>}
          {page==="leaves" && <Leaves/>}
          {page==="antispoof" && <AntiSpoof/>}
          {page==="production" && <Production/>}
          {page==="compliance" && <Compliance/>}
        </div>
      </main>
    </div>
  );
}

const S = {
  layout:   {display:"flex",minHeight:"100vh",background:"#0d1117",color:"#e6edf3",fontFamily:"system-ui,sans-serif"},
  sidebar:  {width:220,background:"#161b22",borderRight:"1px solid #21262d",display:"flex",flexDirection:"column"},
  logo:     {padding:"20px 16px",borderBottom:"1px solid #21262d",display:"flex",alignItems:"center",gap:10},
  logoIcon: {width:36,height:36,background:"linear-gradient(135deg,#00d4aa,#0ea5e9)",borderRadius:10,display:"flex",alignItems:"center",justifyContent:"center",fontSize:18},
  logoText: {fontSize:14,fontWeight:700},
  logoSub:  {fontSize:11,color:"#8b949e"},
  nav:      {padding:"12px 8px",flex:1},
  navItem:  {display:"flex",alignItems:"center",gap:10,padding:"9px 12px",borderRadius:8,cursor:"pointer",color:"#8b949e",fontSize:14,fontWeight:500,border:"none",background:"none",width:"100%",textAlign:"left",marginBottom:2},
  navActive:{background:"rgba(0,212,170,0.12)",color:"#00d4aa"},
  footer:   {padding:"12px 8px",borderTop:"1px solid #21262d"},
  userBox:  {display:"flex",alignItems:"center",gap:8,padding:"8px 12px"},
  avatar:   {width:32,height:32,background:"linear-gradient(135deg,#bc8cff,#0ea5e9)",borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:700},
  main:     {flex:1,display:"flex",flexDirection:"column"},
  topbar:   {padding:"14px 24px",borderBottom:"1px solid #21262d",display:"flex",alignItems:"center",justifyContent:"space-between",background:"rgba(13,17,23,0.9)"},
  badge:    {display:"flex",alignItems:"center",gap:6,background:"rgba(63,185,80,0.12)",border:"1px solid rgba(63,185,80,0.3)",borderRadius:20,padding:"4px 12px",fontSize:12,color:"#3fb950",fontWeight:600},
  dot:      {width:7,height:7,background:"#3fb950",borderRadius:"50%"},
  content:  {padding:24,flex:1,overflowY:"auto"},
};
