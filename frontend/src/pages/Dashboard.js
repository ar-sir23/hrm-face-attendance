import { useState, useEffect } from "react";
import { getToday, getTodayLogs, getCameraStatus } from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [logs,  setLogs]  = useState([]);
  const [cam,   setCam]   = useState(null);

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  const load = () => {
    getToday().then(r=>setStats(r.data)).catch(()=>{});
    getTodayLogs().then(r=>setLogs(r.data.logs||[])).catch(()=>{});
    getCameraStatus().then(r=>setCam(r.data)).catch(()=>{});
  };

  const cards = stats ? [
    {label:"Total Employees", value:stats.total_employees, color:"#0ea5e9", icon:"👥"},
    {label:"Present Today",   value:stats.present,         color:"#3fb950", icon:"✅", sub:stats.present_percentage+"%"},
    {label:"Absent",          value:stats.absent,          color:"#f85149", icon:"❌"},
    {label:"Late Arrivals",   value:stats.late,            color:"#d29922", icon:"⏰"},
  ] : [];

  return (
    <div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:16,marginBottom:24}}>
        {cards.map(c=>(
          <div key={c.label} style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12,padding:"18px 20px",borderTop:"2px solid "+c.color}}>
            <div style={{fontSize:12,color:"#8b949e",marginBottom:8}}>{c.icon} {c.label}</div>
            <div style={{fontSize:32,fontWeight:700,color:c.color,fontFamily:"monospace"}}>{c.value??"-"}</div>
            {c.sub && <div style={{fontSize:12,color:"#8b949e",marginTop:4}}>{c.sub} rate</div>}
          </div>
        ))}
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20}}>
        <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>🕐 Recent Punches</div>
          <div style={{maxHeight:350,overflowY:"auto"}}>
            {logs.length===0
              ? <div style={{padding:32,textAlign:"center",color:"#8b949e"}}>No punches today</div>
              : logs.slice(0,10).map((l,i)=>(
                <div key={i} style={{padding:"12px 20px",borderBottom:"1px solid rgba(33,38,45,0.6)",display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                  <div>
                    <div style={{fontWeight:600,fontSize:14}}>{l.employee_name}</div>
                    <div style={{fontSize:12,color:"#8b949e",marginTop:2}}>
                      {l.punch_time} • {l.method} {l.confidence&&"• "+l.confidence+"% match"}
                    </div>
                  </div>
                  <span style={{padding:"3px 10px",borderRadius:20,fontSize:11,fontWeight:600,
                    background:l.punch_type==="IN"?"rgba(63,185,80,0.15)":"rgba(248,81,73,0.15)",
                    color:l.punch_type==="IN"?"#3fb950":"#f85149"}}>
                    {l.punch_type==="IN"?"✅ IN":"🚪 OUT"}
                  </span>
                </div>
              ))
            }
          </div>
        </div>

        <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>⚙️ System Status</div>
          <div style={{padding:20}}>
            {[
              {label:"Face Recognition", value:"Active",                              color:"#3fb950"},
              {label:"Registered Faces", value:cam?.registered_employees??"-",        color:"#0ea5e9"},
              {label:"AI Model",         value:(cam?.model||"hog").toUpperCase(),     color:"#bc8cff"},
              {label:"Database",         value:"Connected",                           color:"#3fb950"},
              {label:"API Server",       value:"Running :8000",                       color:"#3fb950"},
            ].map(item=>(
              <div key={item.label} style={{display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                <span style={{color:"#8b949e",fontSize:13}}>{item.label}</span>
                <span style={{color:item.color,fontWeight:600,fontSize:13}}>{item.value}</span>
              </div>
            ))}
            {stats&&(
              <div style={{marginTop:20,background:"#0d1117",borderRadius:10,padding:16,border:"1px solid #21262d"}}>
                <div style={{color:"#8b949e",fontSize:12,marginBottom:8}}>Attendance Rate Today</div>
                <div style={{fontSize:28,fontWeight:700,color:"#00d4aa",fontFamily:"monospace"}}>{stats.present_percentage}%</div>
                <div style={{marginTop:8,height:8,background:"#21262d",borderRadius:4,overflow:"hidden"}}>
                  <div style={{height:"100%",width:stats.present_percentage+"%",background:"linear-gradient(90deg,#00d4aa,#0ea5e9)",borderRadius:4}}/>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
