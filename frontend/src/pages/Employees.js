import { useState, useEffect, useRef } from "react";
import { getEmployees, getDepartments, createEmployee, registerFace } from "../api";

export default function Employees() {
  const [tab,   setTab]   = useState("list");
  const [emps,  setEmps]  = useState([]);
  const [depts, setDepts] = useState([]);
  const [form,  setForm]  = useState({employee_id:"",first_name:"",last_name:"",email:"",designation:"",department_id:""});
  const [selEmp,setSelEmp]= useState("");
  const [file,  setFile]  = useState(null);
  const [msg,   setMsg]   = useState(null);
  const fileRef = useRef(null);

  useEffect(()=>{
    getEmployees().then(r=>setEmps(r.data)).catch(()=>{});
    getDepartments().then(r=>setDepts(r.data)).catch(()=>{});
  },[]);

  const showMsg = (type,text) => { setMsg({type,text}); setTimeout(()=>setMsg(null),4000); };

  const handleAdd = async () => {
    try {
      await createEmployee({...form, department_id:form.department_id?parseInt(form.department_id):null});
      showMsg("success","✅ Employee added!");
      setForm({employee_id:"",first_name:"",last_name:"",email:"",designation:"",department_id:""});
      getEmployees().then(r=>setEmps(r.data));
    } catch(e) { showMsg("error","❌ "+(e.response?.data?.detail||e.message)); }
  };

  const handleFace = async () => {
    if (!selEmp||!file) { showMsg("error","Please select employee and photo"); return; }
    try {
      const res = await registerFace(selEmp, file);
      showMsg("success","✅ "+res.data.message);
      getEmployees().then(r=>setEmps(r.data));
    } catch(e) { showMsg("error","❌ "+(e.response?.data?.detail||e.message)); }
  };

  const inp = (label,key,type="text",ph="") => (
    <div key={key}>
      <label style={{display:"block",fontSize:11,color:"#8b949e",fontWeight:600,textTransform:"uppercase",marginBottom:6}}>{label}</label>
      <input type={type} placeholder={ph} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})}
        style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",borderRadius:8,padding:"8px 12px",color:"#e6edf3",fontSize:14}}/>
    </div>
  );

  return (
    <div>
      <div style={{display:"flex",gap:4,background:"#0d1117",padding:4,borderRadius:8,border:"1px solid #21262d",marginBottom:20,width:"fit-content"}}>
        {[["list","👥 List"],["add","➕ Add"],["face","📷 Face"]].map(([id,label])=>(
          <button key={id} onClick={()=>{setTab(id);setMsg(null);}}
            style={{padding:"8px 16px",borderRadius:6,border:"none",cursor:"pointer",fontSize:13,fontWeight:500,
              background:tab===id?"#161b22":"none",color:tab===id?"#e6edf3":"#8b949e"}}>
            {label}
          </button>
        ))}
      </div>

      {msg&&<div style={{padding:"10px 16px",borderRadius:8,marginBottom:16,fontSize:13,
        background:msg.type==="success"?"rgba(63,185,80,0.1)":"rgba(248,81,73,0.1)",
        border:"1px solid "+(msg.type==="success"?"rgba(63,185,80,0.3)":"rgba(248,81,73,0.3)"),
        color:msg.type==="success"?"#3fb950":"#f85149"}}>{msg.text}</div>}

      {tab==="list"&&(
        <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <span style={{fontWeight:600}}>All Employees ({emps.length})</span>
            <div style={{display:"flex",gap:8}}>
              <span style={{fontSize:12,padding:"2px 8px",borderRadius:20,background:"rgba(0,212,170,0.1)",color:"#00d4aa",border:"1px solid rgba(0,212,170,0.3)"}}>✅ {emps.filter(e=>e.face_registered).length} Registered</span>
              <span style={{fontSize:12,padding:"2px 8px",borderRadius:20,background:"rgba(248,81,73,0.1)",color:"#f85149",border:"1px solid rgba(248,81,73,0.3)"}}>❌ {emps.filter(e=>!e.face_registered).length} Pending</span>
            </div>
          </div>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
            <thead>
              <tr>{["Employee","ID","Designation","Email","Face"].map(h=>(
                <th key={h} style={{padding:"10px 16px",textAlign:"left",fontSize:11,color:"#8b949e",textTransform:"uppercase",borderBottom:"1px solid #21262d"}}>{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {emps.length===0
                ? <tr><td colSpan={5} style={{padding:32,textAlign:"center",color:"#8b949e"}}>No employees. Add one first!</td></tr>
                : emps.map(e=>(
                  <tr key={e.employee_id} style={{borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                    <td style={{padding:"12px 16px"}}>
                      <div style={{display:"flex",alignItems:"center",gap:8}}>
                        <div style={{width:32,height:32,borderRadius:"50%",background:"linear-gradient(135deg,#0ea5e9,#bc8cff)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:700}}>
                          {e.first_name[0]}{e.last_name[0]}
                        </div>
                        <span style={{fontWeight:600}}>{e.first_name} {e.last_name}</span>
                      </div>
                    </td>
                    <td style={{padding:"12px 16px",color:"#8b949e",fontFamily:"monospace",fontSize:12}}>{e.employee_id}</td>
                    <td style={{padding:"12px 16px"}}>{e.designation||"-"}</td>
                    <td style={{padding:"12px 16px",color:"#8b949e",fontSize:12}}>{e.email}</td>
                    <td style={{padding:"12px 16px"}}>
                      <span style={{fontSize:11,fontWeight:600,padding:"2px 8px",borderRadius:20,
                        background:e.face_registered?"rgba(0,212,170,0.1)":"rgba(248,81,73,0.1)",
                        color:e.face_registered?"#00d4aa":"#f85149",
                        border:"1px solid "+(e.face_registered?"rgba(0,212,170,0.3)":"rgba(248,81,73,0.3)")}}>
                        {e.face_registered?"✅ Registered":"❌ Pending"}
                      </span>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>
      )}

      {tab==="add"&&(
        <div style={{maxWidth:560,background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>Add New Employee</div>
          <div style={{padding:20}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:12}}>
              {inp("First Name","first_name","text","John")}
              {inp("Last Name","last_name","text","Doe")}
              {inp("Employee ID","employee_id","text","EMP002")}
              {inp("Designation","designation","text","Engineer")}
            </div>
            {inp("Email","email","email","john@company.com")}
            <div style={{marginTop:12}}>
              <label style={{display:"block",fontSize:11,color:"#8b949e",fontWeight:600,textTransform:"uppercase",marginBottom:6}}>Department</label>
              <select value={form.department_id} onChange={e=>setForm({...form,department_id:e.target.value})}
                style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",borderRadius:8,padding:"8px 12px",color:"#e6edf3",fontSize:14}}>
                <option value="">Select Department</option>
                {depts.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <button onClick={handleAdd} style={{marginTop:16,width:"100%",padding:10,background:"#00d4aa",color:"#0d1117",border:"none",borderRadius:8,fontWeight:700,fontSize:14,cursor:"pointer"}}>
              ➕ Add Employee
            </button>
          </div>
        </div>
      )}

      {tab==="face"&&(
        <div style={{maxWidth:560,background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
          <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>Register Employee Face</div>
          <div style={{padding:20}}>
            <div style={{marginBottom:16}}>
              <label style={{display:"block",fontSize:11,color:"#8b949e",fontWeight:600,textTransform:"uppercase",marginBottom:6}}>Select Employee</label>
              <select value={selEmp} onChange={e=>setSelEmp(e.target.value)}
                style={{width:"100%",background:"#0d1117",border:"1px solid #21262d",borderRadius:8,padding:"8px 12px",color:"#e6edf3",fontSize:14}}>
                <option value="">-- Select Employee --</option>
                {emps.map(e=><option key={e.employee_id} value={e.employee_id}>{e.first_name} {e.last_name} ({e.employee_id}) {e.face_registered?"✅":"❌"}</option>)}
              </select>
            </div>
            <div onClick={()=>fileRef.current?.click()}
              style={{border:"2px dashed "+(file?"#3fb950":"#21262d"),borderRadius:10,padding:32,textAlign:"center",cursor:"pointer",
                background:file?"rgba(63,185,80,0.05)":"transparent"}}>
              <input ref={fileRef} type="file" accept="image/*" style={{display:"none"}} onChange={e=>setFile(e.target.files[0])}/>
              {file
                ? <><div style={{fontSize:32,marginBottom:8}}>✅</div><div style={{color:"#3fb950",fontWeight:600}}>{file.name}</div></>
                : <><div style={{fontSize:32,marginBottom:8}}>📁</div><div style={{fontWeight:600}}>Click to upload photo</div><div style={{fontSize:12,color:"#8b949e",marginTop:4}}>JPG or PNG, clear face photo</div></>
              }
            </div>
            <button onClick={handleFace} style={{marginTop:16,width:"100%",padding:10,background:"#00d4aa",color:"#0d1117",border:"none",borderRadius:8,fontWeight:700,fontSize:14,cursor:"pointer"}}>
              📷 Register Face
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
