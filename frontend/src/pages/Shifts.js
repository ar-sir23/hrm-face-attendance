import { useState, useEffect } from "react";

const API = "/api";

export default function Shifts() {
  const [shifts,   setShifts]   = useState([]);
  const [summary,  setSummary]  = useState(null);
  const [overtime, setOvertime] = useState([]);
  const [tab,      setTab]      = useState("overview");
  const [form,     setForm]     = useState({
    employee_id:"", shift_id:"", start_date: new Date().toISOString().slice(0,10)
  });
  const [msg, setMsg] = useState(null);

  useEffect(() => { loadAll(); }, []);

  const loadAll = () => {
    fetch(API + "/shifts/").then(r=>r.json()).then(setShifts).catch(()=>{});
    fetch(API + "/shifts/summary").then(r=>r.json()).then(setSummary).catch(()=>{});
    const today = new Date();
    fetch(API + "/shifts/overtime/monthly?year=" + today.getFullYear() +
          "&month=" + (today.getMonth()+1))
      .then(r=>r.json()).then(d=>setOvertime(d.records||[])).catch(()=>{});
  };

  const showMsg = (type, text) => {
    setMsg({type, text});
    setTimeout(() => setMsg(null), 4000);
  };

  const handleAssign = async () => {
    if (!form.employee_id || !form.shift_id) {
      showMsg("error", "Please fill all fields");
      return;
    }
    try {
      const res = await fetch(API + "/shifts/assign", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({...form, shift_id: parseInt(form.shift_id)})
      });
      const data = await res.json();
      if (res.ok) {
        showMsg("success", "✅ " + data.message);
        loadAll();
      } else {
        showMsg("error", "❌ " + (data.detail || "Failed"));
      }
    } catch(e) {
      showMsg("error", "❌ " + e.message);
    }
  };

  const shiftColors = {
    MORNING: "#f59e0b",
    EVENING: "#0ea5e9",
    NIGHT:   "#8b5cf6",
    GENERAL: "#00d4aa",
    CUSTOM:  "#f85149"
  };

  return (
    <div>
      {/* Tabs */}
      <div style={{display:"flex",gap:4,background:"#0d1117",padding:4,borderRadius:8,
                   border:"1px solid #21262d",marginBottom:20,width:"fit-content"}}>
        {[["overview","📊 Overview"],["assign","👤 Assign Shift"],["overtime","⏱ Overtime"]].map(([id,label])=>(
          <button key={id} onClick={()=>setTab(id)}
            style={{padding:"8px 16px",borderRadius:6,border:"none",cursor:"pointer",
                    fontSize:13,fontWeight:500,
                    background:tab===id?"#161b22":"none",
                    color:tab===id?"#e6edf3":"#8b949e"}}>
            {label}
          </button>
        ))}
      </div>

      {msg && (
        <div style={{padding:"10px 16px",borderRadius:8,marginBottom:16,fontSize:13,
          background:msg.type==="success"?"rgba(63,185,80,0.1)":"rgba(248,81,73,0.1)",
          border:"1px solid "+(msg.type==="success"?"rgba(63,185,80,0.3)":"rgba(248,81,73,0.3)"),
          color:msg.type==="success"?"#3fb950":"#f85149"}}>
          {msg.text}
        </div>
      )}

      {/* Overview */}
      {tab==="overview" && (
        <div>
          {/* Shift cards */}
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:16,marginBottom:24}}>
            {shifts.map(s => (
              <div key={s.id} style={{background:"#161b22",border:"1px solid #21262d",
                                      borderRadius:12,padding:"18px 20px",
                                      borderTop:"3px solid "+(shiftColors[s.shift_type]||"#00d4aa")}}>
                <div style={{fontSize:12,color:"#8b949e",marginBottom:8}}>
                  {s.shift_type==="MORNING"?"🌅":s.shift_type==="EVENING"?"🌆":s.shift_type==="NIGHT"?"🌙":"💼"}
                  {" "}{s.shift_type}
                </div>
                <div style={{fontSize:16,fontWeight:700,marginBottom:8}}>{s.name}</div>
                <div style={{fontSize:13,color:shiftColors[s.shift_type]||"#00d4aa",fontFamily:"monospace",fontWeight:600}}>
                  {s.start_time} → {s.end_time}
                </div>
                <div style={{fontSize:11,color:"#8b949e",marginTop:6}}>
                  Late after: {s.late_after} | OT after: {s.overtime_after_hours}h
                </div>
              </div>
            ))}
          </div>

          {/* Shift summary */}
          {summary && (
            <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
              <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
                📋 Today's Shift Summary — {summary.date}
              </div>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                <thead>
                  <tr>
                    {["Shift","Time","Assigned","Present","Absent"].map(h=>(
                      <th key={h} style={{padding:"10px 16px",textAlign:"left",fontSize:11,
                                          color:"#8b949e",textTransform:"uppercase",
                                          borderBottom:"1px solid #21262d"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {summary.shifts.map((s,i) => (
                    <tr key={i} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                      <td style={{padding:"12px 16px"}}>
                        <span style={{fontWeight:600,color:shiftColors[s.shift_type]||"#00d4aa"}}>
                          {s.shift_name}
                        </span>
                      </td>
                      <td style={{padding:"12px 16px",fontFamily:"monospace",fontSize:12,color:"#8b949e"}}>
                        {s.start_time} → {s.end_time}
                      </td>
                      <td style={{padding:"12px 16px",fontWeight:600}}>{s.total_assigned}</td>
                      <td style={{padding:"12px 16px",color:"#3fb950",fontWeight:600}}>{s.present_today}</td>
                      <td style={{padding:"12px 16px",color:"#f85149",fontWeight:600}}>{s.absent_today}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Assign Shift */}
      {tab==="assign" && (
        <div style={{maxWidth:520,background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
            👤 Assign Employee to Shift
          </div>
          <div style={{padding:20}}>
            {[
              ["Employee ID","employee_id","text","e.g. EMP001"],
              ["Start Date","start_date","date",""],
            ].map(([label,key,type,ph])=>(
              <div key={key} style={{marginBottom:14}}>
                <label style={{display:"block",fontSize:11,color:"#8b949e",fontWeight:600,
                               textTransform:"uppercase",marginBottom:6}}>{label}</label>
                <input type={type} placeholder={ph} value={form[key]}
                  onChange={e=>setForm({...form,[key]:e.target.value})}
                  style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",
                          borderRadius:8,padding:"8px 12px",color:"#e6edf3",fontSize:14}}/>
              </div>
            ))}

            <div style={{marginBottom:16}}>
              <label style={{display:"block",fontSize:11,color:"#8b949e",fontWeight:600,
                             textTransform:"uppercase",marginBottom:6}}>Select Shift</label>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                {shifts.map(s=>(
                  <div key={s.id} onClick={()=>setForm({...form,shift_id:s.id})}
                    style={{padding:"12px 14px",borderRadius:8,cursor:"pointer",
                            border:"2px solid "+(form.shift_id===s.id?shiftColors[s.shift_type]||"#00d4aa":"#21262d"),
                            background:form.shift_id===s.id?"rgba(0,212,170,0.06)":"transparent"}}>
                    <div style={{fontWeight:600,fontSize:13,
                                 color:shiftColors[s.shift_type]||"#00d4aa"}}>{s.name}</div>
                    <div style={{fontSize:11,color:"#8b949e",marginTop:4,fontFamily:"monospace"}}>
                      {s.start_time} → {s.end_time}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button onClick={handleAssign}
              style={{width:"100%",padding:10,background:"#00d4aa",color:"#0d1117",
                      border:"none",borderRadius:8,fontWeight:700,fontSize:14,cursor:"pointer"}}>
              ✅ Assign Shift
            </button>
          </div>
        </div>
      )}

      {/* Overtime */}
      {tab==="overtime" && (
        <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
            ⏱ Monthly Overtime Report
          </div>
          {overtime.length === 0
            ? <div style={{padding:32,textAlign:"center",color:"#8b949e"}}>
                <div style={{fontSize:32,marginBottom:8}}>⏱</div>
                <div>No overtime records this month</div>
              </div>
            : <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                <thead>
                  <tr>
                    {["Employee","OT Days","Total OT Hours","Status"].map(h=>(
                      <th key={h} style={{padding:"10px 16px",textAlign:"left",fontSize:11,
                                          color:"#8b949e",textTransform:"uppercase",
                                          borderBottom:"1px solid #21262d"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {overtime.map((r,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                      <td style={{padding:"12px 16px",fontWeight:600}}>{r.employee_name}</td>
                      <td style={{padding:"12px 16px",color:"#0ea5e9",fontWeight:600}}>
                        {r.overtime_days} days
                      </td>
                      <td style={{padding:"12px 16px",color:"#d29922",fontWeight:700,
                                  fontFamily:"monospace"}}>
                        {Math.round(r.total_overtime_hours * 10) / 10} hrs
                      </td>
                      <td style={{padding:"12px 16px"}}>
                        <span style={{fontSize:11,fontWeight:600,padding:"2px 8px",borderRadius:20,
                          background:"rgba(63,185,80,0.1)",color:"#3fb950",
                          border:"1px solid rgba(63,185,80,0.3)"}}>
                          Pending Approval
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
          }
        </div>
      )}
    </div>
  );
}
