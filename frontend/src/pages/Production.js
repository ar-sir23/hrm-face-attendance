import { useState, useEffect } from "react";

const API = "/api";

const EFF_COLOR = (pct) => {
  if (pct >= 100) return "#3fb950";
  if (pct >= 80)  return "#00d4aa";
  if (pct >= 60)  return "#d29922";
  return "#f85149";
};

export default function Production() {
  const [tab,       setTab]       = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [lines,     setLines]     = useState([]);
  const [performers,setPerformers]= useState([]);
  const [msg,       setMsg]       = useState(null);
  const [loading,   setLoading]   = useState(false);

  const today = new Date().toISOString().slice(0, 10);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year,  setYear]  = useState(new Date().getFullYear());

  const [targetForm, setTargetForm] = useState({
    line_id: "", date: today,
    product_name: "", target_pieces: 500, target_hours: 8
  });
  const [hourlyForm, setHourlyForm] = useState({
    line_id: "", date: today, hour: new Date().getHours(),
    pieces_made: 0, defective: 0,
    workers_present: 0, recorded_by: ""
  });
  const [effForm, setEffForm] = useState({
    employee_id: "", date: today,
    actual_pieces: 0, quality_score: 100,
    incentive_per_piece: 0.5
  });

  useEffect(() => {
    loadAll();
  }, [month, year]);

  const loadAll = () => {
    fetch(API + "/production/dashboard?target_date=" + today)
      .then(r=>r.json()).then(setDashboard).catch(()=>{});
    fetch(API + "/production/lines")
      .then(r=>r.json()).then(setLines).catch(()=>{});
    fetch(API + "/production/top-performers?year=" + year + "&month=" + month)
      .then(r=>r.json()).then(d=>setPerformers(d.top_performers||[])).catch(()=>{});
  };

  const showMsg = (type, text) => {
    setMsg({type, text});
    setTimeout(()=>setMsg(null), 5000);
  };

  const handleSetTarget = async () => {
    if (!targetForm.line_id || !targetForm.product_name) {
      showMsg("error", "Fill all fields"); return;
    }
    setLoading(true);
    try {
      const res  = await fetch(API + "/production/targets", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          ...targetForm,
          line_id:       parseInt(targetForm.line_id),
          target_pieces: parseInt(targetForm.target_pieces),
          target_hours:  parseFloat(targetForm.target_hours)
        })
      });
      const data = await res.json();
      if (res.ok) { showMsg("success","✅ "+data.message); loadAll(); }
      else showMsg("error","❌ "+(data.detail||"Failed"));
    } catch(e) { showMsg("error","❌ "+e.message); }
    setLoading(false);
  };

  const handleHourly = async () => {
    if (!hourlyForm.line_id) { showMsg("error","Select line"); return; }
    setLoading(true);
    try {
      const res  = await fetch(API + "/production/record", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          ...hourlyForm,
          line_id:         parseInt(hourlyForm.line_id),
          hour:            parseInt(hourlyForm.hour),
          pieces_made:     parseInt(hourlyForm.pieces_made),
          defective:       parseInt(hourlyForm.defective),
          workers_present: parseInt(hourlyForm.workers_present)
        })
      });
      const data = await res.json();
      if (res.ok) { showMsg("success","✅ "+data.message); loadAll(); }
      else showMsg("error","❌ "+(data.detail||"Failed"));
    } catch(e) { showMsg("error","❌ "+e.message); }
    setLoading(false);
  };

  const handleEfficiency = async () => {
    if (!effForm.employee_id) { showMsg("error","Enter employee ID"); return; }
    setLoading(true);
    try {
      const res  = await fetch(API + "/production/efficiency", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          ...effForm,
          actual_pieces:       parseInt(effForm.actual_pieces),
          quality_score:       parseFloat(effForm.quality_score),
          incentive_per_piece: parseFloat(effForm.incentive_per_piece)
        })
      });
      const data = await res.json();
      if (res.ok) {
        showMsg("success",
          "✅ " + data.employee_name +
          " — Efficiency: " + data.efficiency_pct + "%" +
          " | Incentive: BDT " + data.incentive_earned);
        loadAll();
      } else showMsg("error","❌ "+(data.detail||"Failed"));
    } catch(e) { showMsg("error","❌ "+e.message); }
    setLoading(false);
  };

  const inp = (label, key, form, setForm, type="text") => (
    <div key={key} style={{marginBottom:10}}>
      <label style={{display:"block",fontSize:11,color:"#8b949e",
                     fontWeight:600,textTransform:"uppercase",marginBottom:4}}>
        {label}
      </label>
      <input type={type} value={form[key]}
        onChange={e=>setForm({...form,[key]:e.target.value})}
        style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",
                borderRadius:8,padding:"7px 10px",color:"#e6edf3",fontSize:13}}/>
    </div>
  );

  const months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];

  return (
    <div>
      {/* Header */}
      <div style={{display:"flex",justifyContent:"space-between",
                   alignItems:"center",marginBottom:20,flexWrap:"wrap",gap:12}}>
        <div style={{display:"flex",gap:4,background:"#0d1117",padding:4,
                     borderRadius:8,border:"1px solid #21262d",flexWrap:"wrap"}}>
          {[
            ["dashboard", "🏭 Dashboard"],
            ["targets",   "🎯 Set Targets"],
            ["hourly",    "⏱ Hourly Entry"],
            ["efficiency","⚡ Efficiency"],
            ["performers","🏆 Top Performers"],
          ].map(([id,label])=>(
            <button key={id} onClick={()=>setTab(id)}
              style={{padding:"8px 12px",borderRadius:6,border:"none",
                      cursor:"pointer",fontSize:12,fontWeight:500,
                      background:tab===id?"#161b22":"none",
                      color:tab===id?"#e6edf3":"#8b949e"}}>
              {label}
            </button>
          ))}
        </div>
        <div style={{display:"flex",gap:8}}>
          <select value={month} onChange={e=>setMonth(parseInt(e.target.value))}
            style={{background:"#161b22",border:"1px solid #21262d",borderRadius:8,
                    padding:"6px 10px",color:"#e6edf3",fontSize:12}}>
            {months.map((m,i)=><option key={i+1} value={i+1}>{m}</option>)}
          </select>
          <select value={year} onChange={e=>setYear(parseInt(e.target.value))}
            style={{background:"#161b22",border:"1px solid #21262d",borderRadius:8,
                    padding:"6px 10px",color:"#e6edf3",fontSize:12}}>
            {[2024,2025,2026,2027].map(y=><option key={y} value={y}>{y}</option>)}
          </select>
        </div>
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
      {tab==="dashboard" && dashboard && (
        <div>
          {/* Factory KPIs */}
          <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",
                       gap:14,marginBottom:20}}>
            {[
              {label:"Total Lines",    value:dashboard.total_lines,           color:"#0ea5e9", icon:"🏭"},
              {label:"Target Pieces",  value:dashboard.total_target_pieces?.toLocaleString(), color:"#d29922", icon:"🎯"},
              {label:"Actual Pieces",  value:dashboard.total_actual_pieces?.toLocaleString(), color:"#3fb950", icon:"✅"},
              {label:"Overall Eff.",   value:dashboard.overall_efficiency+"%",color:EFF_COLOR(dashboard.overall_efficiency), icon:"⚡"},
              {label:"Workers Present",value:dashboard.total_present+"/"+dashboard.total_workers, color:"#bc8cff", icon:"👥"},
            ].map(c=>(
              <div key={c.label} style={{background:"#161b22",border:"1px solid #21262d",
                                         borderRadius:12,padding:"14px 16px",
                                         borderTop:"2px solid "+c.color}}>
                <div style={{fontSize:10,color:"#8b949e",marginBottom:6}}>{c.icon} {c.label}</div>
                <div style={{fontSize:20,fontWeight:700,color:c.color}}>{c.value}</div>
              </div>
            ))}
          </div>

          {/* Lines table */}
          <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
            <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
              🏭 Production Lines — {dashboard.date}
            </div>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead>
                <tr>
                  {["Line","Floor","Product","Target","Actual","Efficiency","Quality","Workers"].map(h=>(
                    <th key={h} style={{padding:"8px 14px",textAlign:"left",fontSize:10,
                                        color:"#8b949e",textTransform:"uppercase",
                                        borderBottom:"1px solid #21262d"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dashboard.lines?.length === 0
                  ? <tr><td colSpan={8} style={{padding:24,textAlign:"center",color:"#8b949e"}}>
                      No production data today. Set targets first.
                    </td></tr>
                  : dashboard.lines?.map((line,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                      <td style={{padding:"10px 14px",fontWeight:700,color:"#00d4aa"}}>
                        {line.line_name}
                      </td>
                      <td style={{padding:"10px 14px",color:"#8b949e",fontSize:11}}>
                        {line.floor||"-"}
                      </td>
                      <td style={{padding:"10px 14px"}}>{line.product||"-"}</td>
                      <td style={{padding:"10px 14px",fontFamily:"monospace"}}>
                        {line.target_pieces?.toLocaleString()||"-"}
                      </td>
                      <td style={{padding:"10px 14px",fontFamily:"monospace",
                                  fontWeight:700,color:"#3fb950"}}>
                        {line.actual_pieces?.toLocaleString()||0}
                      </td>
                      <td style={{padding:"10px 14px"}}>
                        <div style={{display:"flex",alignItems:"center",gap:6}}>
                          <div style={{height:6,width:60,background:"#21262d",
                                       borderRadius:3,overflow:"hidden"}}>
                            <div style={{height:"100%",borderRadius:3,
                                         width:Math.min(line.efficiency,100)+"%",
                                         background:EFF_COLOR(line.efficiency)}}/>
                          </div>
                          <span style={{fontWeight:700,fontSize:11,
                                        color:EFF_COLOR(line.efficiency)}}>
                            {line.efficiency}%
                          </span>
                        </div>
                      </td>
                      <td style={{padding:"10px 14px",
                                  color:line.quality_score>=95?"#3fb950":"#d29922",
                                  fontWeight:600}}>
                        {line.quality_score}%
                      </td>
                      <td style={{padding:"10px 14px"}}>
                        <span style={{fontSize:11}}>
                          {line.present_workers}/{line.total_workers}
                        </span>
                      </td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Set Targets */}
      {tab==="targets" && (
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20}}>
          <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
            <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
              🎯 Set Daily Production Target
            </div>
            <div style={{padding:20}}>
              <div style={{marginBottom:10}}>
                <label style={{display:"block",fontSize:11,color:"#8b949e",
                               fontWeight:600,textTransform:"uppercase",marginBottom:4}}>
                  Select Line
                </label>
                <select value={targetForm.line_id}
                  onChange={e=>setTargetForm({...targetForm,line_id:e.target.value})}
                  style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",
                          borderRadius:8,padding:"7px 10px",color:"#e6edf3",fontSize:13}}>
                  <option value="">-- Select Line --</option>
                  {lines.map(l=>(
                    <option key={l.id} value={l.id}>{l.name} ({l.code})</option>
                  ))}
                </select>
              </div>
              {inp("Date","date",targetForm,setTargetForm,"date")}
              {inp("Product Name","product_name",targetForm,setTargetForm)}
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                {inp("Target Pieces","target_pieces",targetForm,setTargetForm,"number")}
                {inp("Target Hours","target_hours",targetForm,setTargetForm,"number")}
              </div>
              <button onClick={handleSetTarget} disabled={loading}
                style={{width:"100%",marginTop:8,padding:10,background:"#00d4aa",
                        color:"#0d1117",border:"none",borderRadius:8,
                        fontWeight:700,fontSize:13,cursor:"pointer"}}>
                🎯 Set Target
              </button>
            </div>
          </div>

          {/* Today's targets */}
          <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
            <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
              📋 Today's Targets
            </div>
            <div style={{padding:16}}>
              {lines.map(line=>{
                const lineData = dashboard?.lines?.find(l=>l.line_name===line.name);
                return (
                  <div key={line.id} style={{padding:"10px 12px",marginBottom:8,
                                             background:"#0d1117",borderRadius:8,
                                             border:"1px solid #21262d"}}>
                    <div style={{display:"flex",justifyContent:"space-between",
                                 marginBottom:4}}>
                      <span style={{fontWeight:600,color:"#00d4aa",fontSize:13}}>
                        {line.name}
                      </span>
                      <span style={{fontSize:11,color:"#8b949e"}}>{line.floor}</span>
                    </div>
                    {lineData?.target_pieces ? (
                      <>
                        <div style={{fontSize:12,color:"#8b949e"}}>
                          Target: {lineData.target_pieces?.toLocaleString()} pcs
                          {" | "}Product: {lineData.product}
                        </div>
                        <div style={{marginTop:6,height:4,background:"#21262d",
                                     borderRadius:2,overflow:"hidden"}}>
                          <div style={{height:"100%",borderRadius:2,
                                       width:Math.min(lineData.efficiency,100)+"%",
                                       background:EFF_COLOR(lineData.efficiency)}}/>
                        </div>
                        <div style={{fontSize:10,color:EFF_COLOR(lineData.efficiency),
                                     marginTop:2}}>
                          {lineData.efficiency}% achieved
                        </div>
                      </>
                    ) : (
                      <div style={{fontSize:11,color:"#8b949e"}}>No target set</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Hourly Entry */}
      {tab==="hourly" && (
        <div style={{maxWidth:500,background:"#161b22",
                     border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
            ⏱ Hourly Production Entry
          </div>
          <div style={{padding:20}}>
            <div style={{marginBottom:10}}>
              <label style={{display:"block",fontSize:11,color:"#8b949e",
                             fontWeight:600,textTransform:"uppercase",marginBottom:4}}>
                Production Line
              </label>
              <select value={hourlyForm.line_id}
                onChange={e=>setHourlyForm({...hourlyForm,line_id:e.target.value})}
                style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",
                        borderRadius:8,padding:"7px 10px",color:"#e6edf3",fontSize:13}}>
                <option value="">-- Select Line --</option>
                {lines.map(l=><option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
              {inp("Date","date",hourlyForm,setHourlyForm,"date")}
              {inp("Hour (0-23)","hour",hourlyForm,setHourlyForm,"number")}
              {inp("Pieces Made","pieces_made",hourlyForm,setHourlyForm,"number")}
              {inp("Defective","defective",hourlyForm,setHourlyForm,"number")}
              {inp("Workers Present","workers_present",hourlyForm,setHourlyForm,"number")}
              {inp("Recorded By","recorded_by",hourlyForm,setHourlyForm)}
            </div>
            <div style={{background:"#0d1117",borderRadius:8,padding:12,
                         margin:"12px 0",border:"1px solid #21262d"}}>
              <div style={{fontSize:11,color:"#8b949e",marginBottom:6}}>Preview</div>
              <div style={{display:"flex",gap:16,fontSize:13}}>
                <span>Good: <b style={{color:"#3fb950"}}>
                  {Math.max(0, hourlyForm.pieces_made - hourlyForm.defective)}
                </b></span>
                <span>Defect rate: <b style={{color:"#f85149"}}>
                  {hourlyForm.pieces_made > 0
                    ? Math.round(hourlyForm.defective/hourlyForm.pieces_made*100)
                    : 0}%
                </b></span>
              </div>
            </div>
            <button onClick={handleHourly} disabled={loading}
              style={{width:"100%",padding:10,background:"#00d4aa",color:"#0d1117",
                      border:"none",borderRadius:8,fontWeight:700,
                      fontSize:13,cursor:"pointer"}}>
              ⏱ Record Production
            </button>
          </div>
        </div>
      )}

      {/* Efficiency */}
      {tab==="efficiency" && (
        <div style={{maxWidth:480,background:"#161b22",
                     border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>
            ⚡ Record Worker Efficiency
          </div>
          <div style={{padding:20}}>
            {inp("Employee ID","employee_id",effForm,setEffForm)}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
              {inp("Date","date",effForm,setEffForm,"date")}
              {inp("Actual Pieces","actual_pieces",effForm,setEffForm,"number")}
              {inp("Quality Score %","quality_score",effForm,setEffForm,"number")}
              {inp("Incentive/Piece (BDT)","incentive_per_piece",effForm,setEffForm,"number")}
            </div>
            <button onClick={handleEfficiency} disabled={loading}
              style={{width:"100%",marginTop:8,padding:10,background:"#00d4aa",
                      color:"#0d1117",border:"none",borderRadius:8,
                      fontWeight:700,fontSize:13,cursor:"pointer"}}>
              ⚡ Record Efficiency
            </button>
          </div>
        </div>
      )}

      {/* Top Performers */}
      {tab==="performers" && (
        <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",
                       display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <span style={{fontWeight:600}}>🏆 Top Performers</span>
            <span style={{fontSize:12,color:"#8b949e"}}>
              {months[month-1]} {year}
            </span>
          </div>
          {performers.length === 0
            ? <div style={{padding:32,textAlign:"center",color:"#8b949e"}}>
                <div style={{fontSize:32,marginBottom:8}}>🏆</div>
                <div>No efficiency records yet</div>
                <div style={{fontSize:12,marginTop:4}}>
                  Record worker efficiency to see top performers
                </div>
              </div>
            : <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                <thead>
                  <tr>
                    {["Rank","Employee","Avg Efficiency","Total Pieces","Incentive","Days"].map(h=>(
                      <th key={h} style={{padding:"10px 16px",textAlign:"left",
                                          fontSize:11,color:"#8b949e",
                                          textTransform:"uppercase",
                                          borderBottom:"1px solid #21262d"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {performers.map((p,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                      <td style={{padding:"12px 16px",fontWeight:700,fontSize:16,
                                  color:i===0?"#ffd700":i===1?"#c0c0c0":
                                        i===2?"#cd7f32":"#8b949e"}}>
                        #{i+1}
                      </td>
                      <td style={{padding:"12px 16px",fontWeight:600}}>
                        {p.employee_name}
                      </td>
                      <td style={{padding:"12px 16px"}}>
                        <div style={{display:"flex",alignItems:"center",gap:8}}>
                          <div style={{height:6,width:70,background:"#21262d",
                                       borderRadius:3,overflow:"hidden"}}>
                            <div style={{height:"100%",borderRadius:3,
                                         width:Math.min(p.avg_efficiency,100)+"%",
                                         background:EFF_COLOR(p.avg_efficiency)}}/>
                          </div>
                          <span style={{fontWeight:700,
                                        color:EFF_COLOR(p.avg_efficiency)}}>
                            {p.avg_efficiency}%
                          </span>
                        </div>
                      </td>
                      <td style={{padding:"12px 16px",fontFamily:"monospace",
                                  fontWeight:600}}>
                        {p.total_pieces?.toLocaleString()}
                      </td>
                      <td style={{padding:"12px 16px",color:"#00d4aa",
                                  fontWeight:700}}>
                        BDT {p.total_incentive?.toLocaleString()}
                      </td>
                      <td style={{padding:"12px 16px",color:"#8b949e"}}>
                        {p.days_recorded} days
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
