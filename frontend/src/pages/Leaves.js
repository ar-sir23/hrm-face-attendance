import { useState, useEffect } from "react";

const API = "/api";

const LEAVE_TYPES = [
  "ANNUAL", "SICK", "CASUAL", "MATERNITY",
  "PATERNITY", "EMERGENCY", "UNPAID"
];

const LEAVE_COLORS = {
  ANNUAL:    "#00d4aa",
  SICK:      "#f85149",
  CASUAL:    "#0ea5e9",
  MATERNITY: "#bc8cff",
  PATERNITY: "#3fb950",
  EMERGENCY: "#d29922",
  UNPAID:    "#8b949e"
};

const STATUS_COLORS = {
  PENDING:   "#d29922",
  APPROVED:  "#3fb950",
  REJECTED:  "#f85149",
  CANCELLED: "#8b949e"
};

export default function Leaves() {
  const [tab,      setTab]      = useState("dashboard");
  const [summary,  setSummary]  = useState(null);
  const [pending,  setPending]  = useState([]);
  const [balance,  setBalance]  = useState(null);
  const [myApps,   setMyApps]   = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [msg,      setMsg]      = useState(null);
  const [loading,  setLoading]  = useState(false);

  const [applyForm, setApplyForm] = useState({
    employee_id: "", leave_type: "ANNUAL",
    start_date: "", end_date: "", reason: "",
    contact_number: "", handover_to: ""
  });
  const [balEmpId, setBalEmpId] = useState("");
  const [myEmpId,  setMyEmpId]  = useState("");

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = () => {
    fetch(API + "/leaves/summary")
      .then(r=>r.json()).then(setSummary).catch(()=>{});
    fetch(API + "/leaves/applications/pending")
      .then(r=>r.json()).then(d=>setPending(d.applications||[])).catch(()=>{});
    fetch(API + "/leaves/holidays")
      .then(r=>r.json()).then(setHolidays).catch(()=>{});
  };

  const showMsg = (type, text) => {
    setMsg({type, text});
    setTimeout(()=>setMsg(null), 5000);
  };

  const handleApply = async () => {
    if (!applyForm.employee_id || !applyForm.start_date ||
        !applyForm.end_date || !applyForm.reason) {
      showMsg("error", "Please fill all required fields");
      return;
    }
    setLoading(true);
    try {
      const res  = await fetch(API + "/leaves/apply", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(applyForm)
      });
      const data = await res.json();
      if (res.ok) {
        showMsg("success", "✅ " + data.message +
                " (" + data.total_days + " days)");
        setApplyForm({...applyForm, reason:"", start_date:"", end_date:""});
        loadDashboard();
      } else {
        showMsg("error", "❌ " + (data.detail || "Failed"));
      }
    } catch(e) { showMsg("error","❌ "+e.message); }
    setLoading(false);
  };

  const handleBalance = async () => {
    if (!balEmpId) { showMsg("error","Enter employee ID"); return; }
    try {
      const res  = await fetch(API + "/leaves/balance/" + balEmpId);
      const data = await res.json();
      if (res.ok) setBalance(data);
      else showMsg("error","❌ "+(data.detail||"Not found"));
    } catch(e) { showMsg("error","❌ "+e.message); }
  };

  const handleMyApps = async () => {
    if (!myEmpId) { showMsg("error","Enter employee ID"); return; }
    try {
      const res  = await fetch(API + "/leaves/applications/" + myEmpId);
      const data = await res.json();
      if (res.ok) setMyApps(data.applications||[]);
      else showMsg("error","❌ "+(data.detail||"Not found"));
    } catch(e) { showMsg("error","❌ "+e.message); }
  };

  const handleApprove = async (id) => {
    const by = prompt("Approved by (your name):");
    if (!by) return;
    try {
      const res  = await fetch(API + "/leaves/approve/" + id, {
        method: "PUT",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({action_by: by})
      });
      const data = await res.json();
      if (res.ok) {
        showMsg("success", "✅ " + data.message);
        loadDashboard();
      } else showMsg("error","❌ "+(data.detail||"Failed"));
    } catch(e) { showMsg("error","❌ "+e.message); }
  };

  const handleReject = async (id) => {
    const by     = prompt("Rejected by (your name):");
    if (!by) return;
    const reason = prompt("Rejection reason:");
    try {
      const res  = await fetch(API + "/leaves/reject/" + id, {
        method: "PUT",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({action_by: by, reason: reason||""})
      });
      const data = await res.json();
      if (res.ok) {
        showMsg("success", "Leave rejected");
        loadDashboard();
      } else showMsg("error","❌ "+(data.detail||"Failed"));
    } catch(e) { showMsg("error","❌ "+e.message); }
  };

  const inp = (label, key, type="text", ph="", required=false) => (
    <div key={key} style={{marginBottom:12}}>
      <label style={{display:"block",fontSize:11,color:"#8b949e",
                     fontWeight:600,textTransform:"uppercase",marginBottom:5}}>
        {label} {required && <span style={{color:"#f85149"}}>*</span>}
      </label>
      {type === "textarea"
        ? <textarea placeholder={ph} value={applyForm[key]}
            onChange={e=>setApplyForm({...applyForm,[key]:e.target.value})}
            rows={3}
            style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",
                    borderRadius:8,padding:"8px 12px",color:"#e6edf3",
                    fontSize:13,resize:"vertical"}}/>
        : <input type={type} placeholder={ph} value={applyForm[key]}
            onChange={e=>setApplyForm({...applyForm,[key]:e.target.value})}
            style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",
                    borderRadius:8,padding:"8px 12px",color:"#e6edf3",fontSize:13}}/>
      }
    </div>
  );

  return (
    <div>
      {/* Tabs */}
      <div style={{display:"flex",gap:4,background:"#0d1117",padding:4,
                   borderRadius:8,border:"1px solid #21262d",
                   marginBottom:20,width:"fit-content",flexWrap:"wrap"}}>
        {[
          ["dashboard", "📊 Dashboard"],
          ["apply",     "📝 Apply Leave"],
          ["pending",   "⏳ Pending (" + pending.length + ")"],
          ["balance",   "💰 Balance"],
          ["my",        "📋 My Leaves"],
          ["holidays",  "🎉 Holidays"],
        ].map(([id,label])=>(
          <button key={id} onClick={()=>setTab(id)}
            style={{padding:"8px 14px",borderRadius:6,border:"none",
                    cursor:"pointer",fontSize:12,fontWeight:500,
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

      {/* Dashboard */}
      {tab==="dashboard" && (
        <div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",
                       gap:16,marginBottom:24}}>
            {[
              {label:"Pending Approvals",  value:summary?.pending_applications??0,  color:"#d29922", icon:"⏳"},
              {label:"On Leave Today",     value:summary?.employees_on_leave??0,     color:"#f85149", icon:"🏖"},
              {label:"Total Applications", value:summary?.total_applications??0,     color:"#0ea5e9", icon:"📋"},
            ].map(c=>(
              <div key={c.label} style={{background:"#161b22",border:"1px solid #21262d",
                                         borderRadius:12,padding:"18px 20px",
                                         borderTop:"2px solid "+c.color}}>
                <div style={{fontSize:11,color:"#8b949e",marginBottom:8}}>{c.icon} {c.label}</div>
                <div style={{fontSize:32,fontWeight:700,color:c.color,
                             fontFamily:"monospace"}}>{c.value}</div>
              </div>
            ))}
          </div>

          {/* Leave type legend */}
          <div style={{background:"#161b22",border:"1px solid #21262d",
                       borderRadius:12,padding:20,marginBottom:20}}>
            <div style={{fontWeight:600,marginBottom:16}}>📌 Leave Types</div>
            <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12}}>
              {[
                {type:"ANNUAL",    days:18,  desc:"Earned leave"},
                {type:"SICK",      days:14,  desc:"With medical cert"},
                {type:"CASUAL",    days:10,  desc:"Short notice"},
                {type:"MATERNITY", days:112, desc:"16 weeks"},
                {type:"PATERNITY", days:7,   desc:"New father"},
                {type:"EMERGENCY", days:5,   desc:"Urgent situations"},
                {type:"UNPAID",    days:30,  desc:"Without pay"},
              ].map(t=>(
                <div key={t.type} style={{background:"#0d1117",borderRadius:8,
                                          padding:"10px 12px",
                                          borderLeft:"3px solid "+(LEAVE_COLORS[t.type]||"#8b949e")}}>
                  <div style={{fontWeight:600,fontSize:12,
                               color:LEAVE_COLORS[t.type]||"#8b949e"}}>{t.type}</div>
                  <div style={{fontSize:11,color:"#8b949e",marginTop:4}}>
                    {t.days} days/year
                  </div>
                  <div style={{fontSize:10,color:"#8b949e"}}>{t.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent pending */}
          {pending.length > 0 && (
            <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
              <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",
                           fontWeight:600,color:"#d29922"}}>
                ⏳ Pending Approvals ({pending.length})
              </div>
              {pending.slice(0,5).map((app,i)=>(
                <div key={i} style={{padding:"12px 20px",
                                     borderBottom:"1px solid rgba(33,38,45,0.5)",
                                     display:"flex",alignItems:"center",
                                     justifyContent:"space-between",gap:12}}>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600}}>{app.employee_name}</div>
                    <div style={{fontSize:12,color:"#8b949e",marginTop:2}}>
                      <span style={{color:LEAVE_COLORS[app.leave_type]||"#8b949e",
                                    fontWeight:600}}>{app.leave_type}</span>
                      {" • "}{app.start_date} to {app.end_date}
                      {" • "}{app.total_days} days
                    </div>
                    <div style={{fontSize:11,color:"#8b949e",marginTop:2}}>
                      Reason: {app.reason}
                    </div>
                  </div>
                  <div style={{display:"flex",gap:8}}>
                    <button onClick={()=>handleApprove(app.id)}
                      style={{padding:"6px 12px",background:"rgba(63,185,80,0.15)",
                              color:"#3fb950",border:"1px solid rgba(63,185,80,0.3)",
                              borderRadius:6,cursor:"pointer",fontSize:12,fontWeight:600}}>
                      ✅ Approve
                    </button>
                    <button onClick={()=>handleReject(app.id)}
                      style={{padding:"6px 12px",background:"rgba(248,81,73,0.15)",
                              color:"#f85149",border:"1px solid rgba(248,81,73,0.3)",
                              borderRadius:6,cursor:"pointer",fontSize:12,fontWeight:600}}>
                      ❌ Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Apply Leave */}
      {tab==="apply" && (
        <div style={{maxWidth:560,background:"#161b22",
                     border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
            📝 Apply for Leave
          </div>
          <div style={{padding:20}}>
            {inp("Employee ID","employee_id","text","e.g. EMP001",true)}

            <div style={{marginBottom:12}}>
              <label style={{display:"block",fontSize:11,color:"#8b949e",
                             fontWeight:600,textTransform:"uppercase",marginBottom:5}}>
                Leave Type <span style={{color:"#f85149"}}>*</span>
              </label>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
                {LEAVE_TYPES.map(t=>(
                  <div key={t} onClick={()=>setApplyForm({...applyForm,leave_type:t})}
                    style={{padding:"8px 12px",borderRadius:8,cursor:"pointer",
                            border:"2px solid "+(applyForm.leave_type===t?
                              LEAVE_COLORS[t]||"#00d4aa":"#21262d"),
                            background:applyForm.leave_type===t?
                              "rgba(0,212,170,0.06)":"transparent",
                            fontSize:12,fontWeight:600,
                            color:applyForm.leave_type===t?
                              LEAVE_COLORS[t]||"#00d4aa":"#8b949e"}}>
                    {t}
                  </div>
                ))}
              </div>
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
              {inp("Start Date","start_date","date","",true)}
              {inp("End Date","end_date","date","",true)}
            </div>

            {inp("Reason","reason","textarea","Explain reason for leave...",true)}
            {inp("Contact Number","contact_number","text","Phone during leave")}
            {inp("Handover To","handover_to","text","Who will handle your work")}

            <button onClick={handleApply} disabled={loading}
              style={{width:"100%",padding:10,background:"#00d4aa",color:"#0d1117",
                      border:"none",borderRadius:8,fontWeight:700,
                      fontSize:14,cursor:"pointer",marginTop:8}}>
              {loading ? "⏳ Submitting..." : "📝 Submit Leave Application"}
            </button>
          </div>
        </div>
      )}

      {/* Pending */}
      {tab==="pending" && (
        <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",
                       display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <span style={{fontWeight:600}}>⏳ Pending Applications</span>
            <button onClick={loadDashboard}
              style={{padding:"5px 12px",background:"#21262d",color:"#e6edf3",
                      border:"none",borderRadius:6,cursor:"pointer",fontSize:12}}>
              🔄 Refresh
            </button>
          </div>
          {pending.length === 0
            ? <div style={{padding:32,textAlign:"center",color:"#8b949e"}}>
                <div style={{fontSize:32,marginBottom:8}}>✅</div>
                <div>No pending applications</div>
              </div>
            : pending.map((app,i)=>(
              <div key={i} style={{padding:"16px 20px",
                                   borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                <div style={{display:"flex",justifyContent:"space-between",
                             alignItems:"flex-start",marginBottom:8}}>
                  <div>
                    <span style={{fontWeight:700,fontSize:15}}>{app.employee_name}</span>
                    <span style={{marginLeft:10,fontSize:11,fontWeight:600,
                                  padding:"2px 8px",borderRadius:20,
                                  background:(LEAVE_COLORS[app.leave_type]||"#8b949e")+"20",
                                  color:LEAVE_COLORS[app.leave_type]||"#8b949e"}}>
                      {app.leave_type}
                    </span>
                  </div>
                  <div style={{display:"flex",gap:8}}>
                    <button onClick={()=>handleApprove(app.id)}
                      style={{padding:"6px 14px",background:"rgba(63,185,80,0.15)",
                              color:"#3fb950",border:"1px solid rgba(63,185,80,0.3)",
                              borderRadius:6,cursor:"pointer",fontSize:12,fontWeight:600}}>
                      ✅ Approve
                    </button>
                    <button onClick={()=>handleReject(app.id)}
                      style={{padding:"6px 14px",background:"rgba(248,81,73,0.15)",
                              color:"#f85149",border:"1px solid rgba(248,81,73,0.3)",
                              borderRadius:6,cursor:"pointer",fontSize:12,fontWeight:600}}>
                      ❌ Reject
                    </button>
                  </div>
                </div>
                <div style={{fontSize:13,color:"#8b949e",display:"flex",gap:16,flexWrap:"wrap"}}>
                  <span>📅 {app.start_date} → {app.end_date}</span>
                  <span>🗓 {app.total_days} days</span>
                  <span>🕐 Applied: {app.applied_on}</span>
                </div>
                <div style={{fontSize:13,color:"#e6edf3",marginTop:6,
                             background:"#0d1117",padding:"8px 12px",borderRadius:6}}>
                  📝 {app.reason}
                </div>
              </div>
            ))
          }
        </div>
      )}

      {/* Balance */}
      {tab==="balance" && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:20}}>
            <input placeholder="Enter Employee ID (e.g. EMP001)"
              value={balEmpId} onChange={e=>setBalEmpId(e.target.value)}
              style={{flex:1,background:"#161b22",border:"1px solid #21262d",
                      borderRadius:8,padding:"9px 12px",color:"#e6edf3",fontSize:14}}/>
            <button onClick={handleBalance}
              style={{padding:"9px 20px",background:"#0ea5e9",color:"#0d1117",
                      border:"none",borderRadius:8,fontWeight:700,cursor:"pointer"}}>
              🔍 Check Balance
            </button>
          </div>

          {balance && (
            <div>
              <div style={{marginBottom:16,fontWeight:600,fontSize:15}}>
                {balance.employee_name} — Leave Balance {balance.year}
              </div>
              <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16}}>
                {balance.balances.map((b,i)=>(
                  <div key={i} style={{background:"#161b22",border:"1px solid #21262d",
                                       borderRadius:12,padding:16,
                                       borderTop:"3px solid "+(LEAVE_COLORS[b.leave_type]||"#8b949e")}}>
                    <div style={{fontWeight:600,color:LEAVE_COLORS[b.leave_type]||"#8b949e",
                                 fontSize:13,marginBottom:12}}>{b.leave_type}</div>
                    <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
                      <span style={{fontSize:12,color:"#8b949e"}}>Total</span>
                      <span style={{fontWeight:600}}>{b.total_days} days</span>
                    </div>
                    <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
                      <span style={{fontSize:12,color:"#8b949e"}}>Used</span>
                      <span style={{fontWeight:600,color:"#f85149"}}>{b.used_days} days</span>
                    </div>
                    <div style={{display:"flex",justifyContent:"space-between",marginBottom:10}}>
                      <span style={{fontSize:12,color:"#8b949e"}}>Remaining</span>
                      <span style={{fontWeight:700,
                                    color:LEAVE_COLORS[b.leave_type]||"#00d4aa"}}>
                        {b.remaining_days} days
                      </span>
                    </div>
                    <div style={{height:6,background:"#21262d",borderRadius:3,overflow:"hidden"}}>
                      <div style={{height:"100%",borderRadius:3,
                                   width:b.percentage_used+"%",
                                   background:LEAVE_COLORS[b.leave_type]||"#00d4aa",
                                   transition:"width 0.5s"}}/>
                    </div>
                    <div style={{fontSize:10,color:"#8b949e",marginTop:4,textAlign:"right"}}>
                      {b.percentage_used}% used
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* My Leaves */}
      {tab==="my" && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:20}}>
            <input placeholder="Enter Employee ID"
              value={myEmpId} onChange={e=>setMyEmpId(e.target.value)}
              style={{flex:1,background:"#161b22",border:"1px solid #21262d",
                      borderRadius:8,padding:"9px 12px",color:"#e6edf3",fontSize:14}}/>
            <button onClick={handleMyApps}
              style={{padding:"9px 20px",background:"#0ea5e9",color:"#0d1117",
                      border:"none",borderRadius:8,fontWeight:700,cursor:"pointer"}}>
              🔍 Get My Leaves
            </button>
          </div>
          {myApps.length > 0 && (
            <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                <thead>
                  <tr>
                    {["Type","Start","End","Days","Reason","Status","Applied On"].map(h=>(
                      <th key={h} style={{padding:"10px 14px",textAlign:"left",fontSize:11,
                                          color:"#8b949e",textTransform:"uppercase",
                                          borderBottom:"1px solid #21262d"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {myApps.map((app,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                      <td style={{padding:"10px 14px"}}>
                        <span style={{fontSize:11,fontWeight:600,padding:"2px 8px",
                                      borderRadius:20,
                                      background:(LEAVE_COLORS[app.leave_type]||"#8b949e")+"20",
                                      color:LEAVE_COLORS[app.leave_type]||"#8b949e"}}>
                          {app.leave_type}
                        </span>
                      </td>
                      <td style={{padding:"10px 14px",fontFamily:"monospace",fontSize:12}}>
                        {app.start_date}
                      </td>
                      <td style={{padding:"10px 14px",fontFamily:"monospace",fontSize:12}}>
                        {app.end_date}
                      </td>
                      <td style={{padding:"10px 14px",fontWeight:600,textAlign:"center"}}>
                        {app.total_days}
                      </td>
                      <td style={{padding:"10px 14px",color:"#8b949e",fontSize:12,
                                  maxWidth:150,overflow:"hidden",textOverflow:"ellipsis"}}>
                        {app.reason}
                      </td>
                      <td style={{padding:"10px 14px"}}>
                        <span style={{fontSize:11,fontWeight:600,padding:"2px 8px",
                                      borderRadius:20,
                                      background:(STATUS_COLORS[app.status]||"#8b949e")+"20",
                                      color:STATUS_COLORS[app.status]||"#8b949e",
                                      border:"1px solid "+(STATUS_COLORS[app.status]||"#8b949e")+"50"}}>
                          {app.status}
                        </span>
                      </td>
                      <td style={{padding:"10px 14px",fontSize:11,color:"#8b949e"}}>
                        {app.applied_on}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Holidays */}
      {tab==="holidays" && (
        <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16}}>
          {holidays.map((h,i)=>(
            <div key={i} style={{background:"#161b22",border:"1px solid #21262d",
                                  borderRadius:12,padding:16,
                                  borderLeft:"3px solid "+(h.is_optional?"#d29922":"#00d4aa")}}>
              <div style={{fontWeight:600,marginBottom:4}}>{h.name}</div>
              <div style={{fontFamily:"monospace",color:"#00d4aa",fontSize:13,marginBottom:4}}>
                {h.date}
              </div>
              {h.is_optional && (
                <span style={{fontSize:10,padding:"2px 6px",borderRadius:20,
                              background:"rgba(210,153,34,0.15)",color:"#d29922",
                              border:"1px solid rgba(210,153,34,0.3)"}}>
                  Optional
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
