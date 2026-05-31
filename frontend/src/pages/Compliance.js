import { useState, useEffect } from "react";

const API = "/api";

const STATUS_STYLE = (status) => {
  if (!status) return {};
  if (status.includes("COMPLIANT") && !status.includes("NON"))
    return { color: "#3fb950", bg: "rgba(63,185,80,0.1)",
             border: "rgba(63,185,80,0.3)" };
  if (status.includes("VIOLATION") || status.includes("NON"))
    return { color: "#f85149", bg: "rgba(248,81,73,0.1)",
             border: "rgba(248,81,73,0.3)" };
  return { color: "#d29922", bg: "rgba(210,153,34,0.1)",
           border: "rgba(210,153,34,0.3)" };
};

const Badge = ({ status }) => {
  const s = STATUS_STYLE(status);
  return (
    <span style={{ fontSize:11, fontWeight:700, padding:"3px 10px",
                   borderRadius:20, background:s.bg, color:s.color,
                   border:"1px solid "+s.border }}>
      {status}
    </span>
  );
};

const ComplianceCard = ({ check }) => {
  const [open, setOpen] = useState(false);
  const s = STATUS_STYLE(check.status);
  const rate = check.compliance_rate ?? 100;

  return (
    <div style={{ background:"#161b22", border:"1px solid #21262d",
                  borderRadius:12, overflow:"hidden", marginBottom:14 }}>
      <div onClick={() => setOpen(!open)}
        style={{ padding:"16px 20px", cursor:"pointer",
                 borderLeft:"4px solid "+s.color,
                 display:"flex", justifyContent:"space-between",
                 alignItems:"center" }}>
        <div>
          <div style={{ fontWeight:700, fontSize:14, marginBottom:4 }}>
            {check.check}
          </div>
          <div style={{ fontSize:11, color:"#8b949e" }}>{check.law}</div>
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:16 }}>
          <div style={{ textAlign:"right" }}>
            <div style={{ fontSize:22, fontWeight:700, color:s.color,
                          fontFamily:"monospace" }}>
              {rate}%
            </div>
            <div style={{ fontSize:10, color:"#8b949e" }}>compliance</div>
          </div>
          <Badge status={check.status} />
          <span style={{ color:"#8b949e", fontSize:16 }}>
            {open ? "▲" : "▼"}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ height:4, background:"#21262d" }}>
        <div style={{ height:"100%", width:rate+"%",
                      background:s.color, transition:"width 0.5s" }} />
      </div>

      {open && (
        <div style={{ padding:"16px 20px", borderTop:"1px solid #21262d" }}>
          <div style={{ display:"grid",
                        gridTemplateColumns:"repeat(3,1fr)", gap:12,
                        marginBottom:16 }}>
            {[
              ["Total",    check.total_employees, "#e6edf3"],
              ["Compliant",check.compliant ?? (check.total_employees - (check.violations || check.issues_found || 0)), "#3fb950"],
              ["Violations",check.violations ?? check.issues_found ?? 0, "#f85149"],
            ].map(([label,val,color])=>(
              <div key={label} style={{ background:"#0d1117", borderRadius:8,
                                         padding:"10px 12px",
                                         border:"1px solid #21262d",
                                         textAlign:"center" }}>
                <div style={{ fontSize:11, color:"#8b949e", marginBottom:4 }}>
                  {label}
                </div>
                <div style={{ fontSize:20, fontWeight:700, color,
                              fontFamily:"monospace" }}>{val}</div>
              </div>
            ))}
          </div>

          {/* Violations list */}
          {(check.violation_details || check.issue_details)?.length > 0 && (
            <div>
              <div style={{ fontWeight:600, fontSize:12,
                            color:"#f85149", marginBottom:8 }}>
                ❌ Violations / Issues:
              </div>
              <div style={{ maxHeight:200, overflowY:"auto" }}>
                {(check.violation_details || check.issue_details)
                  .map((v, i) => (
                  <div key={i} style={{ padding:"8px 12px",
                                        background:"rgba(248,81,73,0.05)",
                                        borderRadius:6, marginBottom:4,
                                        border:"1px solid rgba(248,81,73,0.15)",
                                        fontSize:12 }}>
                    <span style={{ fontWeight:600 }}>
                      {v.employee_name} ({v.employee_id})
                    </span>
                    {" — "}
                    <span style={{ color:"#f85149" }}>
                      {v.violation || v.issue}
                    </span>
                    {v.date && (
                      <span style={{ color:"#8b949e",
                                     marginLeft:8, fontSize:11 }}>
                        {v.date}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function Compliance() {
  const [tab,        setTab]        = useState("dashboard");
  const [report,     setReport]     = useState(null);
  const [bgmea,      setBgmea]      = useState(null);
  const [audit,      setAudit]      = useState([]);
  const [suspicious, setSuspicious] = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year,  setYear]  = useState(new Date().getFullYear());

  const today = new Date().toISOString().slice(0, 10);
  const [auditStart, setAuditStart] = useState(
    new Date().toISOString().slice(0, 8) + "01");
  const [auditEnd, setAuditEnd] = useState(today);
  const [auditEmpId, setAuditEmpId] = useState("");

  useEffect(() => { loadReport(); }, [month, year]);

  const loadReport = () => {
    setLoading(true);
    const q = "?year=" + year + "&month=" + month;
    fetch(API + "/compliance/full-report" + q)
      .then(r=>r.json()).then(setReport).catch(()=>{})
      .finally(()=>setLoading(false));
    fetch(API + "/compliance/bgmea-report" + q)
      .then(r=>r.json()).then(setBgmea).catch(()=>{});
    fetch(API + "/compliance/suspicious")
      .then(r=>r.json()).then(setSuspicious).catch(()=>{});
  };

  const loadAudit = () => {
    const q = "?start_date=" + auditStart +
              "&end_date=" + auditEnd +
              (auditEmpId ? "&employee_id=" + auditEmpId : "");
    fetch(API + "/compliance/audit-trail" + q)
      .then(r=>r.json()).then(d=>setAudit(d.logs||[])).catch(()=>{});
  };

  const exportJSON = () => {
    window.open(
      API + "/compliance/export-json?year=" + year + "&month=" + month,
      "_blank"
    );
  };

  const months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];

  const overallRate = report?.summary?.overall_compliance_rate ?? 0;
  const overallColor = overallRate >= 95 ? "#3fb950" :
                       overallRate >= 80 ? "#d29922" : "#f85149";

  return (
    <div>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between",
                    alignItems:"center", marginBottom:20,
                    flexWrap:"wrap", gap:12 }}>
        <div style={{ display:"flex", gap:4, background:"#0d1117",
                      padding:4, borderRadius:8,
                      border:"1px solid #21262d", flexWrap:"wrap" }}>
          {[
            ["dashboard", "📊 Compliance"],
            ["bgmea",     "🏛 BGMEA Report"],
            ["audit",     "🔍 Audit Trail"],
            ["suspicious","⚠️ Suspicious"],
          ].map(([id,label])=>(
            <button key={id} onClick={()=>setTab(id)}
              style={{ padding:"8px 14px", borderRadius:6, border:"none",
                       cursor:"pointer", fontSize:12, fontWeight:500,
                       background:tab===id?"#161b22":"none",
                       color:tab===id?"#e6edf3":"#8b949e" }}>
              {label}
            </button>
          ))}
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <select value={month} onChange={e=>setMonth(parseInt(e.target.value))}
            style={{ background:"#161b22", border:"1px solid #21262d",
                     borderRadius:8, padding:"6px 10px",
                     color:"#e6edf3", fontSize:12 }}>
            {months.map((m,i)=>(
              <option key={i+1} value={i+1}>{m}</option>
            ))}
          </select>
          <select value={year} onChange={e=>setYear(parseInt(e.target.value))}
            style={{ background:"#161b22", border:"1px solid #21262d",
                     borderRadius:8, padding:"6px 10px",
                     color:"#e6edf3", fontSize:12 }}>
            {[2024,2025,2026,2027].map(y=>(
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button onClick={exportJSON}
            style={{ padding:"7px 14px", background:"#00d4aa",
                     color:"#0d1117", border:"none", borderRadius:8,
                     fontWeight:700, fontSize:12, cursor:"pointer" }}>
            📥 Export JSON
          </button>
        </div>
      </div>

      {/* Compliance Dashboard */}
      {tab==="dashboard" && (
        <div>
          {loading ? (
            <div style={{ padding:48, textAlign:"center", color:"#8b949e" }}>
              ⏳ Generating compliance report...
            </div>
          ) : report ? (
            <>
              {/* Overall score */}
              <div style={{ background:"#161b22",
                            border:"1px solid #21262d",
                            borderRadius:12, padding:24,
                            marginBottom:20,
                            display:"flex", justifyContent:"space-between",
                            alignItems:"center" }}>
                <div>
                  <div style={{ fontSize:13, color:"#8b949e", marginBottom:4 }}>
                    Overall Compliance Rate
                  </div>
                  <div style={{ fontSize:48, fontWeight:700,
                                color:overallColor,
                                fontFamily:"monospace" }}>
                    {overallRate}%
                  </div>
                  <div style={{ marginTop:8, height:8, width:300,
                                background:"#21262d", borderRadius:4,
                                overflow:"hidden" }}>
                    <div style={{ height:"100%", borderRadius:4,
                                  width:overallRate+"%",
                                  background:overallColor,
                                  transition:"width 0.5s" }} />
                  </div>
                </div>
                <div style={{ textAlign:"right" }}>
                  <div style={{ fontSize:11, color:"#8b949e",
                                marginBottom:8 }}>
                    {report.period?.month_name}
                  </div>
                  <Badge status={report.summary?.status} />
                  <div style={{ marginTop:12, fontSize:13,
                                color:"#8b949e" }}>
                    Total violations:{" "}
                    <span style={{ color:"#f85149", fontWeight:700 }}>
                      {report.summary?.total_violations}
                    </span>
                  </div>
                  <div style={{ fontSize:11, color:"#8b949e", marginTop:4 }}>
                    {report.summary?.total_checks} checks performed
                  </div>
                </div>
              </div>

              {/* Individual checks */}
              {report.checks && Object.values(report.checks).map((check, i) => (
                <ComplianceCard key={i} check={check} />
              ))}
            </>
          ) : (
            <div style={{ padding:48, textAlign:"center", color:"#8b949e" }}>
              <div style={{ fontSize:32, marginBottom:8 }}>📊</div>
              <div>Click Refresh to generate report</div>
              <button onClick={loadReport}
                style={{ marginTop:12, padding:"8px 20px",
                          background:"#00d4aa", color:"#0d1117",
                          border:"none", borderRadius:8,
                          fontWeight:700, cursor:"pointer" }}>
                Generate Report
              </button>
            </div>
          )}
        </div>
      )}

      {/* BGMEA Report */}
      {tab==="bgmea" && bgmea && (
        <div>
          {/* Header card */}
          <div style={{ background:"linear-gradient(135deg,#0d2818,#0d1117)",
                        border:"2px solid #00d4aa", borderRadius:12,
                        padding:24, marginBottom:20 }}>
            <div style={{ display:"flex", justifyContent:"space-between",
                          alignItems:"flex-start" }}>
              <div>
                <div style={{ fontSize:11, color:"#8b949e", marginBottom:4 }}>
                  🏛 BGMEA WORKFORCE COMPLIANCE REPORT
                </div>
                <div style={{ fontSize:20, fontWeight:700,
                              color:"#00d4aa" }}>
                  {bgmea.factory_name}
                </div>
                <div style={{ fontSize:13, color:"#8b949e", marginTop:4 }}>
                  Code: {bgmea.factory_code} | Period: {bgmea.period}
                </div>
              </div>
              <div style={{ fontSize:11, color:"#8b949e",
                            textAlign:"right" }}>
                Generated: {bgmea.generated_at}
              </div>
            </div>
          </div>

          <div style={{ display:"grid",
                        gridTemplateColumns:"1fr 1fr", gap:20 }}>
            {/* Workforce */}
            <div style={{ background:"#161b22",
                          border:"1px solid #21262d",
                          borderRadius:12 }}>
              <div style={{ padding:"14px 20px",
                            borderBottom:"1px solid #21262d",
                            fontWeight:600 }}>
                👥 Workforce Statistics
              </div>
              <div style={{ padding:20 }}>
                {[
                  ["Total Workers",     bgmea.workforce?.total_workers,       "#e6edf3"],
                  ["Working Days",      bgmea.workforce?.working_days,        "#8b949e"],
                  ["Avg Attendance",    bgmea.workforce?.avg_attendance_rate+"%","#3fb950"],
                  ["Total Present Days",bgmea.workforce?.total_present_days,  "#3fb950"],
                  ["Total Absent Days", bgmea.workforce?.total_absent_days,   "#f85149"],
                  ["Total Late Days",   bgmea.workforce?.total_late_days,     "#d29922"],
                ].map(([label,val,color])=>(
                  <div key={label}
                    style={{ display:"flex", justifyContent:"space-between",
                             padding:"8px 0",
                             borderBottom:"1px solid rgba(33,38,45,0.5)" }}>
                    <span style={{ color:"#8b949e", fontSize:13 }}>
                      {label}
                    </span>
                    <span style={{ color, fontWeight:600, fontSize:13 }}>
                      {val}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Wages */}
            <div style={{ background:"#161b22",
                          border:"1px solid #21262d",
                          borderRadius:12 }}>
              <div style={{ padding:"14px 20px",
                            borderBottom:"1px solid #21262d",
                            fontWeight:600 }}>
                💰 Wage Statistics
              </div>
              <div style={{ padding:20 }}>
                {[
                  ["Total Wages Paid",    "BDT "+bgmea.wages?.total_wages_paid?.toLocaleString(), "#00d4aa"],
                  ["Avg Wage/Worker",     "BDT "+bgmea.wages?.avg_wage_per_worker?.toLocaleString(),"#0ea5e9"],
                  ["Minimum Wage (Law)",  "BDT "+bgmea.wages?.minimum_wage_bdt?.toLocaleString(),  "#8b949e"],
                  ["Payroll Records",     bgmea.wages?.payroll_records,                             "#8b949e"],
                  ["Leave Applications",  bgmea.leave?.total_leave_applications,                   "#bc8cff"],
                  ["Total Leave Days",    bgmea.leave?.total_leave_days,                           "#bc8cff"],
                ].map(([label,val,color])=>(
                  <div key={label}
                    style={{ display:"flex", justifyContent:"space-between",
                             padding:"8px 0",
                             borderBottom:"1px solid rgba(33,38,45,0.5)" }}>
                    <span style={{ color:"#8b949e", fontSize:13 }}>
                      {label}
                    </span>
                    <span style={{ color, fontWeight:600, fontSize:13 }}>
                      {val}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Compliance statement */}
          <div style={{ marginTop:20, background:"rgba(0,212,170,0.06)",
                        border:"1px solid rgba(0,212,170,0.3)",
                        borderRadius:12, padding:20 }}>
            <div style={{ fontWeight:600, color:"#00d4aa",
                          marginBottom:8 }}>
              ✅ Compliance Statement
            </div>
            <div style={{ fontSize:13, color:"#8b949e", lineHeight:1.6 }}>
              {bgmea.compliance_statement}
            </div>
          </div>
        </div>
      )}

      {/* Audit Trail */}
      {tab==="audit" && (
        <div>
          {/* Filters */}
          <div style={{ background:"#161b22",
                        border:"1px solid #21262d",
                        borderRadius:12, padding:20,
                        marginBottom:20 }}>
            <div style={{ fontWeight:600, marginBottom:14 }}>
              🔍 Audit Trail Filters
            </div>
            <div style={{ display:"flex", gap:12,
                          alignItems:"flex-end", flexWrap:"wrap" }}>
              {[
                ["Start Date", auditStart, setAuditStart, "date"],
                ["End Date",   auditEnd,   setAuditEnd,   "date"],
                ["Employee ID (optional)", auditEmpId, setAuditEmpId, "text"],
              ].map(([label, val, setter, type])=>(
                <div key={label}>
                  <label style={{ display:"block", fontSize:11,
                                  color:"#8b949e", fontWeight:600,
                                  textTransform:"uppercase",
                                  marginBottom:5 }}>
                    {label}
                  </label>
                  <input type={type} value={val}
                    onChange={e=>setter(e.target.value)}
                    style={{ background:"#0d1117",
                             border:"1px solid #21262d",
                             borderRadius:8, padding:"7px 10px",
                             color:"#e6edf3", fontSize:13, width:160 }}/>
                </div>
              ))}
              <button onClick={loadAudit}
                style={{ padding:"9px 20px", background:"#00d4aa",
                         color:"#0d1117", border:"none", borderRadius:8,
                         fontWeight:700, cursor:"pointer" }}>
                🔍 Search
              </button>
            </div>
          </div>

          {/* Results */}
          <div style={{ background:"#161b22",
                        border:"1px solid #21262d",
                        borderRadius:12 }}>
            <div style={{ padding:"14px 20px",
                          borderBottom:"1px solid #21262d",
                          display:"flex",
                          justifyContent:"space-between" }}>
              <span style={{ fontWeight:600 }}>Audit Logs</span>
              <span style={{ fontSize:12, color:"#8b949e" }}>
                {audit.length} records
              </span>
            </div>
            {audit.length === 0
              ? <div style={{ padding:32, textAlign:"center",
                              color:"#8b949e" }}>
                  Click Search to load audit trail
                </div>
              : <div style={{ maxHeight:500, overflowY:"auto" }}>
                  <table style={{ width:"100%",
                                  borderCollapse:"collapse",
                                  fontSize:12 }}>
                    <thead>
                      <tr>
                        {["#","Employee","Action","Time","Method",
                          "Confidence","Location","Department"].map(h=>(
                          <th key={h}
                            style={{ padding:"8px 14px", textAlign:"left",
                                     fontSize:10, color:"#8b949e",
                                     textTransform:"uppercase",
                                     borderBottom:"1px solid #21262d",
                                     position:"sticky", top:0,
                                     background:"#161b22" }}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {audit.map((log, i) => (
                        <tr key={i}
                          style={{ borderBottom:"1px solid rgba(33,38,45,0.4)" }}>
                          <td style={{ padding:"8px 14px",
                                       color:"#8b949e", fontSize:10 }}>
                            {log.log_id}
                          </td>
                          <td style={{ padding:"8px 14px", fontWeight:600 }}>
                            {log.employee_name}
                          </td>
                          <td style={{ padding:"8px 14px" }}>
                            <span style={{ fontSize:10, fontWeight:600,
                                           padding:"2px 8px", borderRadius:20,
                                           background:log.action==="IN"?
                                             "rgba(63,185,80,0.15)":
                                             "rgba(248,81,73,0.15)",
                                           color:log.action==="IN"?
                                             "#3fb950":"#f85149" }}>
                              {log.action}
                            </span>
                          </td>
                          <td style={{ padding:"8px 14px",
                                       fontFamily:"monospace",
                                       fontSize:11, color:"#8b949e" }}>
                            {new Date(log.timestamp)
                              .toLocaleString()}
                          </td>
                          <td style={{ padding:"8px 14px",
                                       fontSize:11, color:"#8b949e" }}>
                            {log.method}
                          </td>
                          <td style={{ padding:"8px 14px",
                                       color: log.confidence >= 90?"#3fb950":
                                              log.confidence >= 70?"#d29922":
                                              "#f85149",
                                       fontWeight:600, fontSize:11 }}>
                            {log.confidence ?
                              log.confidence.toFixed(1)+"%" : "-"}
                          </td>
                          <td style={{ padding:"8px 14px",
                                       fontSize:11, color:"#8b949e" }}>
                            {log.location || "-"}
                          </td>
                          <td style={{ padding:"8px 14px",
                                       fontSize:11, color:"#8b949e" }}>
                            {log.department || "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
            }
          </div>
        </div>
      )}

      {/* Suspicious */}
      {tab==="suspicious" && (
        <div>
          <div style={{ background:"#161b22",
                        border:"1px solid #21262d",
                        borderRadius:12 }}>
            <div style={{ padding:"14px 20px",
                          borderBottom:"1px solid #21262d",
                          display:"flex",
                          justifyContent:"space-between",
                          alignItems:"center" }}>
              <span style={{ fontWeight:600 }}>
                ⚠️ Suspicious Activities
              </span>
              <div style={{ display:"flex", gap:10 }}>
                <span style={{ fontSize:12, color:"#8b949e" }}>
                  Today: {new Date().toLocaleDateString()}
                </span>
                <button onClick={loadReport}
                  style={{ padding:"4px 12px", background:"#21262d",
                           color:"#e6edf3", border:"none",
                           borderRadius:6, cursor:"pointer",
                           fontSize:12 }}>
                  🔄 Refresh
                </button>
              </div>
            </div>

            {!suspicious ? (
              <div style={{ padding:32, textAlign:"center",
                            color:"#8b949e" }}>
                Loading...
              </div>
            ) : suspicious.total === 0 ? (
              <div style={{ padding:48, textAlign:"center" }}>
                <div style={{ fontSize:40, marginBottom:12 }}>✅</div>
                <div style={{ fontWeight:700, color:"#3fb950",
                              fontSize:16 }}>
                  No Suspicious Activity
                </div>
                <div style={{ color:"#8b949e", fontSize:13,
                              marginTop:8 }}>
                  All attendance records look normal today
                </div>
              </div>
            ) : (
              <div>
                <div style={{ padding:"12px 20px",
                              background:"rgba(210,153,34,0.08)",
                              borderBottom:"1px solid rgba(210,153,34,0.2)",
                              fontSize:13, color:"#d29922",
                              fontWeight:600 }}>
                  ⚠️ {suspicious.total} items need review — {suspicious.status}
                </div>
                {suspicious.items?.map((item, i) => (
                  <div key={i}
                    style={{ padding:"14px 20px",
                             borderBottom:"1px solid rgba(33,38,45,0.5)",
                             display:"flex", justifyContent:"space-between",
                             alignItems:"center" }}>
                    <div>
                      <div style={{ fontWeight:600, fontSize:14,
                                    marginBottom:4 }}>
                        {item.employee_name}
                        <span style={{ fontSize:11, color:"#8b949e",
                                       marginLeft:8 }}>
                          ({item.employee_id})
                        </span>
                      </div>
                      <div style={{ fontSize:12, color:"#8b949e" }}>
                        {item.detail}
                      </div>
                    </div>
                    <div style={{ display:"flex", gap:10,
                                  alignItems:"center" }}>
                      <span style={{ fontSize:10, fontWeight:700,
                                     padding:"3px 10px", borderRadius:20,
                                     background:item.severity==="HIGH"?
                                       "rgba(248,81,73,0.15)":
                                       item.severity==="MEDIUM"?
                                       "rgba(210,153,34,0.15)":
                                       "rgba(139,148,158,0.15)",
                                     color:item.severity==="HIGH"?
                                       "#f85149":
                                       item.severity==="MEDIUM"?
                                       "#d29922":"#8b949e" }}>
                        {item.severity}
                      </span>
                      <span style={{ fontSize:10, color:"#8b949e",
                                     background:"rgba(0,0,0,0.3)",
                                     padding:"3px 8px",
                                     borderRadius:20 }}>
                        {item.type}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
