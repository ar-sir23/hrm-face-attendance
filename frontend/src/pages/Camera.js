import { useState, useRef, useCallback } from "react";
import { facePunch } from "../api";

export default function Camera() {
  const videoRef  = useRef(null);
  const streamRef = useRef(null);
  const [active,   setActive]   = useState(false);
  const [scanning, setScanning] = useState(false);
  const [result,   setResult]   = useState(null);
  const [logs,     setLogs]     = useState([]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({video:true});
      videoRef.current.srcObject = stream;
      streamRef.current = stream;
      setActive(true);
    } catch {
      setResult({type:"error", message:"Camera access denied!"});
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(t=>t.stop());
    setActive(false);
  };

  const doRecognize = async (file) => {
    setScanning(true);
    try {
      const res  = await facePunch(file, "Main Gate");
      const data = res.data;
      if (data.success && data.records?.length>0) {
        const rec = data.records[0];
        setLogs(p=>[{name:rec.employee_name, type:rec.punch_type, time:new Date().toLocaleTimeString(), conf:rec.confidence}, ...p.slice(0,9)]);
        setResult({type:"success", ...rec});
      } else {
        setResult({type:"fail", message:data.message||"No face recognized"});
      }
    } catch(e) {
      setResult({type:"error", message:"Server error: "+e.message});
    }
    setScanning(false);
  };

  const captureAndPunch = useCallback(async () => {
    if (!videoRef.current||scanning) return;
    const canvas = document.createElement("canvas");
    canvas.width  = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    canvas.getContext("2d").drawImage(videoRef.current,0,0);
    const blob = await new Promise(res=>canvas.toBlob(res,"image/jpeg"));
    doRecognize(new File([blob],"capture.jpg",{type:"image/jpeg"}));
  }, [scanning]);

  const B = (bg,color,flex=1) => ({flex,padding:"10px 16px",background:bg,color,border:"none",borderRadius:8,fontWeight:600,fontSize:13,cursor:"pointer"});

  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20}}>
      <div>
        <div style={{background:"#0a0e13",border:"2px solid "+(active?"#00d4aa":"#21262d"),borderRadius:12,aspectRatio:"4/3",display:"flex",alignItems:"center",justifyContent:"center",position:"relative",overflow:"hidden"}}>
          <video ref={videoRef} autoPlay playsInline muted style={{width:"100%",height:"100%",objectFit:"cover",display:active?"block":"none"}}/>
          {!active&&<div style={{textAlign:"center",color:"#8b949e"}}><div style={{fontSize:48,marginBottom:12}}>📷</div><div style={{fontWeight:600}}>Camera Off</div></div>}
          {scanning&&<div style={{position:"absolute",inset:0,background:"rgba(0,0,0,0.6)",display:"flex",alignItems:"center",justifyContent:"center",color:"#00d4aa",fontWeight:700,fontSize:16}}>🔍 Scanning...</div>}
          {active&&!scanning&&<div style={{position:"absolute",bottom:10,left:"50%",transform:"translateX(-50%)",background:"rgba(0,0,0,0.7)",borderRadius:20,padding:"4px 14px",fontSize:12,color:"#00d4aa",fontWeight:600}}>👁 Camera Active</div>}
        </div>

        <div style={{display:"flex",gap:8,marginTop:12}}>
          {!active
            ? <button onClick={startCamera} style={B("#00d4aa","#0d1117")}>📷 Start Camera</button>
            : <><button onClick={captureAndPunch} disabled={scanning} style={B("#00d4aa","#0d1117")}>{scanning?"⏳ Scanning...":"🔍 Scan Face"}</button>
               <button onClick={stopCamera} style={B("#21262d","#e6edf3",0)}>Stop</button></>
          }
        </div>

        <label style={{display:"block",marginTop:12,padding:"10px 16px",background:"#161b22",border:"1px solid #21262d",borderRadius:8,fontWeight:600,fontSize:13,cursor:"pointer",textAlign:"center",color:"#8b949e"}}>
          📁 Upload Photo to Punch
          <input type="file" accept="image/*" style={{display:"none"}} onChange={e=>e.target.files[0]&&doRecognize(e.target.files[0])}/>
        </label>

        {result&&(
          <div style={{marginTop:12,padding:16,borderRadius:10,border:"1px solid",
            borderColor:result.type==="success"?"rgba(63,185,80,0.3)":"rgba(248,81,73,0.3)",
            background:result.type==="success"?"rgba(63,185,80,0.08)":"rgba(248,81,73,0.08)"}}>
            {result.type==="success"
              ? <><div style={{color:"#3fb950",fontWeight:700,marginBottom:6}}>✅ Face Recognized!</div>
                  <div style={{fontSize:18,fontWeight:700}}>{result.employee_name}</div>
                  <div style={{fontSize:13,color:"#8b949e",marginTop:4}}>{result.punch_type==="IN"?"✅ Entry":"🚪 Exit"} • {new Date().toLocaleTimeString()}</div>
                  {result.confidence&&<div style={{fontSize:12,color:"#00d4aa",marginTop:4}}>Confidence: {result.confidence}%</div>}</>
              : <><div style={{color:"#f85149",fontWeight:700,marginBottom:4}}>❌ Not Recognized</div>
                  <div style={{color:"#8b949e",fontSize:13}}>{result.message}</div></>
            }
          </div>
        )}
      </div>

      <div style={{background:"#161b22",border:"1px solid #21262d",borderRadius:12}}>
        <div style={{padding:"14px 20px",borderBottom:"1px solid #21262d",fontWeight:600}}>📋 Live Log</div>
        {logs.length===0
          ? <div style={{padding:32,textAlign:"center",color:"#8b949e"}}><div style={{fontSize:32,marginBottom:8}}>📭</div><div>No records yet</div></div>
          : logs.map((l,i)=>(
            <div key={i} style={{padding:"12px 16px",borderBottom:"1px solid rgba(33,38,45,0.6)",display:"flex",alignItems:"center",gap:12}}>
              <div style={{width:32,height:32,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",
                background:l.type==="IN"?"rgba(63,185,80,0.15)":"rgba(248,81,73,0.15)",
                color:l.type==="IN"?"#3fb950":"#f85149",fontSize:16}}>
                {l.type==="IN"?"→":"←"}
              </div>
              <div style={{flex:1}}>
                <div style={{fontWeight:600,fontSize:13}}>{l.name}</div>
                <div style={{fontSize:11,color:"#8b949e"}}>{l.time}{l.conf&&" • "+l.conf+"%"}</div>
              </div>
              <span style={{fontSize:11,fontWeight:600,padding:"2px 8px",borderRadius:20,
                background:l.type==="IN"?"rgba(63,185,80,0.15)":"rgba(248,81,73,0.15)",
                color:l.type==="IN"?"#3fb950":"#f85149"}}>
                {l.type}
              </span>
            </div>
          ))
        }
      </div>
    </div>
  );
}
