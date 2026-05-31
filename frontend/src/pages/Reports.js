import { useState, useEffect } from "react";
import { getTodayDetails, getLateToday, getToday } from "../api";

const downloadExcel = (url, filename) => {
  fetch("/api/export/" + url)
    .then(res => res.blob())
    .then(blob => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
    })
    .catch(err => alert("Download failed: " + err.message));
};

export default function Reports() {
  const [details, setDetails] = useState([]);
  const [late,    setLate]    = useState([]);
  const [stats,   setStats]   = useState(null);
  const [month,   setMonth]   = useState(new Date().getMonth() + 1);
  const [year,    setYear]    = useState(new Date().getFullYear());

  useEffect(() => {
    getTodayDetails().then(r => setDetails(r.data.records || [])).catch(() => {});
    getLateToday().then(r => setLate(r.data.employees || [])).catch(() => {});
    getToday().then(r => setStats(r.data)).catch(() => {});
  }, []);

  const sColor = s => ({
    PRESENT:  "#3fb950",
    LATE:     "#d29922",
    ABSENT:   "#f85149",
    HALF_DAY: "#0ea5e9"
  }[s] || "#8b949e");

  const months = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
  ];

  return (
    <div>

      {/* ── Export Buttons ── */}
      <div style={{background:"#161b22", border:"1px solid #21262d", borderRadius:12, padding:20, marginBottom:24}}>
        <div style={{fontWeight:700, fontSize:15, marginBottom:16}}>📥 Export Reports to Excel</div>

        {/* Month / Year selector */}
        <div style={{display:"flex", gap:12, marginBottom:16, alignItems:"center"}}>
          <div>
            <label style={{display:"block", fontSize:11, color:"#8b949e", fontWeight:600, textTransform:"uppercase", marginBottom:6}}>Month</label>
            <select value={month} onChange={e => setMonth(parseInt(e.target.value))}
              style={{background:"#0d1117", border:"1px solid #21262d", borderRadius:8, padding:"8px 12px", color:"#e6edf3", fontSize:13}}>
              {months.map((m, i) => <option key={i+1} value={i+1}>{m}</option>)}
            </select>
          </div>
          <div>
            <label style={{display:"block", fontSize:11, color:"#8b949e", fontWeight:600, textTransform:"uppercase", marginBottom:6}}>Year</label>
            <select value={year} onChange={e => setYear(parseInt(e.target.value))}
              style={{background:"#0d1117", border:"1px solid #21262d", borderRadius:8, padding:"8px 12px", color:"#e6edf3", fontSize:13}}>
              {[2024, 2025, 2026, 2027].map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        </div>

        {/* Download buttons */}
        <div style={{display:"flex", gap:12, flexWrap:"wrap"}}>
          <button
            onClick={() => downloadExcel("daily", "daily_attendance_" + new Date().toISOString().slice(0,10) + ".xlsx")}
            style={{padding:"10px 20px", background:"#3fb950", color:"#0d1117",
                    border:"none", borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer"}}>
            📥 Today's Attendance
          </button>
          <button
            onClick={() => downloadExcel(
              "monthly?year=" + year + "&month=" + month,
              "attendance_" + year + "_" + String(month).padStart(2,"0") + ".xlsx"
            )}
            style={{padding:"10px 20px", background:"#0ea5e9", color:"#0d1117",
                    border:"none", borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer"}}>
            📅 Monthly Attendance
          </button>
          <button
            onClick={() => downloadExcel(
              "salary-sheet?year=" + year + "&month=" + month,
              "salary_sheet_" + year + "_" + String(month).padStart(2,"0") + ".xlsx"
            )}
            style={{padding:"10px 20px", background:"#00d4aa", color:"#0d1117",
                    border:"none", borderRadius:8, fontWeight:700, fontSize:13, cursor:"pointer"}}>
            💰 Salary Sheet
          </button>
        </div>

        <div style={{marginTop:12, fontSize:12, color:"#8b949e"}}>
          ℹ️ Monthly Attendance and Salary Sheet will use the selected Month and Year above.
        </div>
      </div>

      {/* ── Summary Cards ── */}
      <div style={{display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:16, marginBottom:24}}>
        {[
          {label:"Present Today", value:stats?.present  ?? "-", color:"#3fb950", icon:"✅"},
          {label:"Late Arrivals", value:late.length,             color:"#d29922", icon:"⏰"},
          {label:"Absent Today",  value:stats?.absent   ?? "-", color:"#f85149", icon:"❌"},
        ].map(c => (
          <div key={c.label} style={{background:"#161b22", border:"1px solid #21262d", borderRadius:12,
                                     padding:"18px 20px", borderTop:"2px solid "+c.color}}>
            <div style={{fontSize:12, color:"#8b949e", marginBottom:8}}>{c.icon} {c.label}</div>
            <div style={{fontSize:32, fontWeight:700, color:c.color, fontFamily:"monospace"}}>{c.value}</div>
          </div>
        ))}
      </div>

      {/* ── Today's Detail Table ── */}
      <div style={{background:"#161b22", border:"1px solid #21262d", borderRadius:12, marginBottom:20}}>
        <div style={{padding:"14px 20px", borderBottom:"1px solid #21262d", fontWeight:600}}>
          📋 Today's Attendance Detail
        </div>
        <table style={{width:"100%", borderCollapse:"collapse", fontSize:13}}>
          <thead>
            <tr>
              {["Employee","Status","First In","Last Out","Work Hours","Late"].map(h => (
                <th key={h} style={{padding:"10px 16px", textAlign:"left", fontSize:11,
                                    color:"#8b949e", textTransform:"uppercase",
                                    borderBottom:"1px solid #21262d"}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {details.length === 0
              ? <tr><td colSpan={6} style={{padding:32, textAlign:"center", color:"#8b949e"}}>No records today</td></tr>
              : details.map((d, i) => (
                <tr key={i} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                  <td style={{padding:"12px 16px", fontWeight:600}}>{d.employee_name}</td>
                  <td style={{padding:"12px 16px"}}>
                    <span style={{fontSize:11, fontWeight:600, padding:"2px 8px", borderRadius:20,
                                  background:sColor(d.status)+"20", color:sColor(d.status),
                                  border:"1px solid "+sColor(d.status)+"50"}}>
                      {d.status}
                    </span>
                  </td>
                  <td style={{padding:"12px 16px", fontFamily:"monospace", color:"#3fb950"}}>{d.first_in  || "-"}</td>
                  <td style={{padding:"12px 16px", fontFamily:"monospace", color:"#f85149"}}>{d.last_out || "-"}</td>
                  <td style={{padding:"12px 16px", fontFamily:"monospace"}}>{d.work_hours ? d.work_hours + " hrs" : "-"}</td>
                  <td style={{padding:"12px 16px"}}>
                    {d.is_late
                      ? <span style={{color:"#d29922", fontSize:12}}>⏰ Late</span>
                      : <span style={{color:"#3fb950", fontSize:12}}>✅ On time</span>}
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>

      {/* ── Late Employees ── */}
      {late.length > 0 && (
        <div style={{background:"#161b22", border:"1px solid #21262d", borderRadius:12}}>
          <div style={{padding:"14px 20px", borderBottom:"1px solid #21262d",
                       fontWeight:600, color:"#d29922"}}>
            ⏰ Late Arrivals Today
          </div>
          {late.map((e, i) => (
            <div key={i} style={{padding:"12px 20px", borderBottom:"1px solid rgba(33,38,45,0.5)",
                                  display:"flex", justifyContent:"space-between", alignItems:"center"}}>
              <span style={{fontWeight:600}}>{e.employee_name}</span>
              <div style={{display:"flex", gap:16, fontSize:13, color:"#8b949e"}}>
                <span>Arrived: <span style={{color:"#d29922", fontFamily:"monospace"}}>{e.arrival_time}</span></span>
                <span>Late by: <span style={{color:"#f85149", fontWeight:600}}>{e.late_minutes} min</span></span>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
