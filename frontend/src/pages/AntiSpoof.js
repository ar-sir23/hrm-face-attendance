import { useState, useRef, useEffect, useCallback } from "react";

const API = "/api";

export default function AntiSpoof() {
  const videoRef   = useRef(null);
  const streamRef  = useRef(null);
  const intervalRef = useRef(null);

  const [sessionId,  setSessionId]  = useState(null);
  const [active,     setActive]     = useState(false);
  const [checking,   setChecking]   = useState(false);
  const [result,     setResult]     = useState(null);
  const [liveness,   setLiveness]   = useState(null);
  const [logs,       setLogs]       = useState([]);
  const [blinks,     setBlinks]     = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [instruction,setInstruction]= useState("Start camera to begin");
  const [phase,      setPhase]      = useState("idle");
  // idle → checking → verified → punched

  const addLog = (msg, type="info") => {
    const time = new Date().toLocaleTimeString();
    setLogs(p => [{msg, type, time}, ...p.slice(0,19)]);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {width:640, height:480, facingMode:"user"}
      });
      videoRef.current.srcObject = stream;
      streamRef.current = stream;
      setActive(true);

      // Get new session
      const res  = await fetch(API + "/liveness/new-session", {method:"POST"});
      const data = await res.json();
      setSessionId(data.session_id);
      setPhase("checking");
      setBlinks(0);
      setConfidence(0);
      setInstruction("👤 Position your face in the camera");
      addLog("Camera started. Session: " + data.session_id, "info");
      startLivenessCheck(data.session_id);
    } catch(e) {
      addLog("Camera error: " + e.message, "error");
    }
  };

  const stopCamera = () => {
    stopLivenessCheck();
    streamRef.current?.getTracks().forEach(t=>t.stop());
    setActive(false);
    setPhase("idle");
    setSessionId(null);
    setLiveness(null);
    setResult(null);
    setBlinks(0);
    setConfidence(0);
    setInstruction("Start camera to begin");
  };

  const captureFrame = useCallback(() => {
    if (!videoRef.current) return null;
    const canvas = document.createElement("canvas");
    canvas.width  = videoRef.current.videoWidth  || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
    return new Promise(res => canvas.toBlob(res, "image/jpeg", 0.8));
  }, []);

  const startLivenessCheck = (sid) => {
    intervalRef.current = setInterval(async () => {
      const blob = await captureFrame();
      if (!blob) return;
      const form = new FormData();
      form.append("image_base64",
        await blobToBase64(blob));
      try {
        const res  = await fetch(API + "/liveness/check-frame-base64?" +
          new URLSearchParams({
            image_base64: await blobToBase64(blob),
            session_id:   sid
          }), {method:"POST",
               headers:{"Content-Type":"application/json"},
               body: JSON.stringify({
                 image_base64: await blobToBase64(blob),
                 session_id: sid
               })});
        // Use file upload approach instead
        const form2 = new FormData();
        form2.append("file", blob, "frame.jpg");
        form2.append("session_id", sid);
        const res2  = await fetch(API + "/liveness/check-frame", {
          method: "POST", body: form2
        });
        const data = await res2.json();
        setBlinks(data.blinks || 0);
        setConfidence(data.confidence || 0);
        setInstruction(data.instruction || "");
        setLiveness(data);

        if (data.live && data.blinks >= 1) {
          stopLivenessCheck();
          setPhase("verified");
          setInstruction("✅ Liveness verified! Recording attendance...");
          addLog("Liveness verified! Confidence: " + data.confidence + "%", "success");
          await recordAttendance(sid);
        }
      } catch(e) {
        addLog("Check error: " + e.message, "error");
      }
    }, 800);
  };

  const stopLivenessCheck = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const blobToBase64 = (blob) => new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.readAsDataURL(blob);
  });

  const recordAttendance = async (sid) => {
    setChecking(true);
    try {
      const blob = await captureFrame();
      if (!blob) return;
      const form = new FormData();
      form.append("file",            blob, "capture.jpg");
      form.append("session_id",      sid);
      form.append("location",        "Main Gate");
      form.append("required_blinks", "1");
      const res  = await fetch(API + "/liveness/verify-and-punch", {
        method: "POST", body: form
      });
      const data = await res.json();
      setResult(data);
      if (data.success) {
        setPhase("punched");
        const rec = data.records?.[0];
        addLog("✅ Attendance recorded: " +
               (rec?.employee_name || "Unknown") +
               " — " + (rec?.punch_type || ""), "success");
        setInstruction("✅ Done! Attendance recorded.");
      } else {
        setPhase("checking");
        addLog("❌ " + data.message, "error");
        setInstruction(data.message || "Try again");
        // Restart liveness check
        const res2  = await fetch(API + "/liveness/new-session", {method:"POST"});
        const data2 = await res2.json();
        setSessionId(data2.session_id);
        setBlinks(0);
        setConfidence(0);
        startLivenessCheck(data2.session_id);
      }
    } catch(e) {
      addLog("Punch error: " + e.message, "error");
    }
    setChecking(false);
  };

  useEffect(() => () => { stopCamera(); }, []);

  const phaseColor = {
    idle:     "#8b949e",
    checking: "#d29922",
    verified: "#0ea5e9",
    punched:  "#3fb950"
  }[phase] || "#8b949e";

  const phaseLabel = {
    idle:     "Idle",
    checking: "Checking Liveness...",
    verified: "Verified!",
    punched:  "Attendance Recorded!"
  }[phase] || "Idle";

  return (
    <div>
      <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:20}}>

        {/* Camera Panel */}
        <div>
          {/* Camera feed */}
          <div style={{background:"#0a0e13",
                       border:"2px solid " + phaseColor,
                       borderRadius:12, aspectRatio:"4/3",
                       display:"flex", alignItems:"center",
                       justifyContent:"center", position:"relative",
                       overflow:"hidden", transition:"border-color 0.3s"}}>
            <video ref={videoRef} autoPlay playsInline muted
              style={{width:"100%", height:"100%", objectFit:"cover",
                      display:active?"block":"none"}}/>
            {!active && (
              <div style={{textAlign:"center", color:"#8b949e"}}>
                <div style={{fontSize:64, marginBottom:16}}>🛡️</div>
                <div style={{fontWeight:700, fontSize:16}}>Anti-Spoofing Camera</div>
                <div style={{fontSize:12, marginTop:8, color:"#8b949e"}}>
                  Blink detection + Liveness verification
                </div>
              </div>
            )}

            {/* Overlay indicators */}
            {active && (
              <>
                {/* Phase badge */}
                <div style={{position:"absolute", top:12, left:12,
                             background:"rgba(0,0,0,0.75)",
                             backdropFilter:"blur(8px)",
                             borderRadius:20, padding:"4px 12px",
                             fontSize:11, fontWeight:600,
                             color:phaseColor, border:"1px solid "+phaseColor}}>
                  {phaseLabel}
                </div>

                {/* Blink counter */}
                <div style={{position:"absolute", top:12, right:12,
                             background:"rgba(0,0,0,0.75)",
                             borderRadius:20, padding:"4px 12px",
                             fontSize:11, fontWeight:600, color:"#e6edf3"}}>
                  👁 Blinks: {blinks}
                </div>

                {/* Confidence bar */}
                <div style={{position:"absolute", bottom:0, left:0, right:0,
                             background:"rgba(0,0,0,0.7)", padding:"8px 12px"}}>
                  <div style={{fontSize:11, color:"#8b949e", marginBottom:4}}>
                    Liveness Score
                  </div>
                  <div style={{height:6, background:"rgba(255,255,255,0.1)",
                               borderRadius:3, overflow:"hidden"}}>
                    <div style={{height:"100%", borderRadius:3,
                                 width:confidence+"%",
                                 background:"linear-gradient(90deg,#d29922,#00d4aa)",
                                 transition:"width 0.3s"}}/>
                  </div>
                  <div style={{fontSize:10, color:"#8b949e", marginTop:2}}>
                    {confidence}% confidence
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Instruction box */}
          <div style={{marginTop:12, padding:"12px 16px",
                       background:"#161b22", borderRadius:10,
                       border:"1px solid " + phaseColor,
                       fontSize:14, fontWeight:600,
                       color:phaseColor, textAlign:"center",
                       transition:"border-color 0.3s, color 0.3s"}}>
            {instruction}
          </div>

          {/* Buttons */}
          <div style={{display:"flex", gap:8, marginTop:12}}>
            {!active
              ? <button onClick={startCamera}
                  style={{flex:1, padding:"11px", background:"#00d4aa",
                          color:"#0d1117", border:"none", borderRadius:8,
                          fontWeight:700, fontSize:14, cursor:"pointer"}}>
                  🛡️ Start Anti-Spoof Check
                </button>
              : <button onClick={stopCamera}
                  style={{flex:1, padding:"11px", background:"rgba(248,81,73,0.15)",
                          color:"#f85149", border:"1px solid rgba(248,81,73,0.3)",
                          borderRadius:8, fontWeight:700, fontSize:14, cursor:"pointer"}}>
                  ⏹ Stop
                </button>
            }
          </div>

          {/* Result card */}
          {result && (
            <div style={{marginTop:12, padding:16, borderRadius:10,
                         border:"1px solid",
                         borderColor:result.success?"rgba(63,185,80,0.3)":"rgba(248,81,73,0.3)",
                         background:result.success?"rgba(63,185,80,0.08)":"rgba(248,81,73,0.08)"}}>
              {result.success ? (
                <>
                  <div style={{color:"#3fb950", fontWeight:700, marginBottom:8, fontSize:15}}>
                    ✅ Attendance Recorded!
                  </div>
                  {result.records?.map((rec, i) => (
                    <div key={i}>
                      <div style={{fontSize:18, fontWeight:700}}>{rec.employee_name}</div>
                      <div style={{fontSize:13, color:"#8b949e", marginTop:4}}>
                        {rec.punch_type==="IN" ? "✅ Entry" : "🚪 Exit"} •{" "}
                        {new Date().toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                  <div style={{marginTop:8, display:"flex", gap:12, fontSize:12}}>
                    <span style={{color:"#00d4aa"}}>
                      🛡️ Liveness: {result.liveness_score}%
                    </span>
                    <span style={{color:"#8b949e"}}>
                      👁 Blinks: {result.blinks_detected}
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <div style={{color:"#f85149", fontWeight:700, marginBottom:4}}>
                    ❌ Failed
                  </div>
                  <div style={{color:"#8b949e", fontSize:13}}>{result.message}</div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Info + Logs Panel */}
        <div>
          {/* How it works */}
          <div style={{background:"#161b22", border:"1px solid #21262d",
                       borderRadius:12, padding:20, marginBottom:16}}>
            <div style={{fontWeight:700, fontSize:15, marginBottom:16}}>
              🛡️ Anti-Spoofing Checks
            </div>
            {[
              {
                icon: "👁",
                title: "Blink Detection",
                desc: "Detects real eye blinks using Eye Aspect Ratio (EAR). Photos and videos can't blink.",
                color: "#00d4aa",
                check: liveness?.checks?.blink_detected
              },
              {
                icon: "📏",
                title: "Face Size Check",
                desc: "Verifies face is large enough — prevents attacks from distance.",
                color: "#0ea5e9",
                check: liveness?.checks?.face_size_ok
              },
              {
                icon: "🔬",
                title: "Texture Analysis",
                desc: "LBP algorithm detects real skin texture vs printed paper.",
                color: "#bc8cff",
                check: liveness?.checks?.texture_ok
              },
              {
                icon: "🔄",
                title: "Micro-Movement",
                desc: "Tracks natural head micro-movements. Static images fail this.",
                color: "#d29922",
                check: liveness?.checks?.movement_ok
              },
            ].map((item, i) => (
              <div key={i} style={{display:"flex", gap:12, marginBottom:14,
                                   padding:"10px 12px", borderRadius:8,
                                   background:"#0d1117",
                                   border:"1px solid " + (item.check ? item.color+"40" : "#21262d")}}>
                <div style={{fontSize:20, flexShrink:0}}>{item.icon}</div>
                <div style={{flex:1}}>
                  <div style={{display:"flex", justifyContent:"space-between",
                               alignItems:"center", marginBottom:4}}>
                    <span style={{fontWeight:600, fontSize:13, color:item.color}}>
                      {item.title}
                    </span>
                    {liveness && (
                      <span style={{fontSize:11, fontWeight:600,
                                    color:item.check?"#3fb950":"#f85149"}}>
                        {item.check ? "✅ PASS" : "❌ FAIL"}
                      </span>
                    )}
                  </div>
                  <div style={{fontSize:11, color:"#8b949e", lineHeight:1.5}}>
                    {item.desc}
                  </div>
                </div>
              </div>
            ))}

            {/* Live stats */}
            {liveness && (
              <div style={{background:"#0d1117", borderRadius:8,
                           padding:"10px 14px", marginTop:8,
                           border:"1px solid #21262d"}}>
                <div style={{fontWeight:600, fontSize:12,
                             color:"#8b949e", marginBottom:8}}>
                  Live Detection Data
                </div>
                {[
                  ["EAR Value",     liveness.ear],
                  ["Blink Count",   liveness.blinks],
                  ["Confidence",    liveness.confidence + "%"],
                  ["Texture Score", liveness.checks?.texture_score],
                  ["Movement",      liveness.checks?.movement_range],
                ].map(([label, val]) => val !== undefined && (
                  <div key={label}
                    style={{display:"flex", justifyContent:"space-between",
                            fontSize:12, padding:"3px 0",
                            borderBottom:"1px solid rgba(33,38,45,0.5)"}}>
                    <span style={{color:"#8b949e"}}>{label}</span>
                    <span style={{fontFamily:"monospace", color:"#00d4aa"}}>
                      {val}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Live log */}
          <div style={{background:"#161b22", border:"1px solid #21262d",
                       borderRadius:12}}>
            <div style={{padding:"12px 16px", borderBottom:"1px solid #21262d",
                         fontWeight:600, fontSize:13}}>
              📋 Detection Log
            </div>
            <div style={{maxHeight:250, overflowY:"auto"}}>
              {logs.length === 0
                ? <div style={{padding:20, textAlign:"center",
                               color:"#8b949e", fontSize:13}}>
                    No events yet
                  </div>
                : logs.map((log, i) => (
                  <div key={i}
                    style={{padding:"8px 16px",
                            borderBottom:"1px solid rgba(33,38,45,0.4)",
                            display:"flex", gap:10, alignItems:"flex-start"}}>
                    <span style={{fontSize:10, color:"#8b949e",
                                  fontFamily:"monospace", flexShrink:0,
                                  marginTop:2}}>
                      {log.time}
                    </span>
                    <span style={{fontSize:12,
                                  color:log.type==="success"?"#3fb950":
                                        log.type==="error"?"#f85149":"#8b949e"}}>
                      {log.msg}
                    </span>
                  </div>
                ))
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
