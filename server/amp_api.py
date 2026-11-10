#!/usr/bin/env python3
"""Minimal CubeCoders AMP client for the create-pack server (stdlib only).

Talks to the ADS controller over HTTP and reaches instances through ADS's proxy
(/API/ADSModule/Servers/<InstanceID>/API/...), so only the controller port is needed.

Credentials: AMP_USER / AMP_PASS env vars, or (default) read from the AMP container's
USERNAME/PASSWORD env over SSH, which is where amp-dockerized keeps the panel login.

Subcommands (all take the instance name):
  status   <instance>                 print app state
  stop     <instance>                 start the instance process if needed, stop the app, wait for Stopped
  start    <instance>                 start the app, wait for Ready (fails on Failed/timeout)
  neoforge <instance> <version>       ensure NeoForge server type + version; run AMP's updater if changed
  settings <instance> <json-file>     apply {"Node": "value"} AMP settings
  autostart <instance> on|off         toggle "start instance on boot" + "start app with instance"
  create   <instance> <friendly> <amp-web-port>  create a new Minecraft instance (one-time). The port
                                      is the instance's own AMP management port (KidsMC01 uses 8081),
                                      NOT the game port — that comes from amp-settings.json.
  schedule <instance>                 ensure the nightly 04:30 stop->backup->start job (idempotent)
  console  <instance> <command>       send a console command (e.g. "chunky start")
"""
import json, os, subprocess, sys, time, urllib.request, uuid

AMP_URL = os.environ.get("AMP_URL", "http://10.0.0.180:8080")
UNRAID = os.environ.get("UNRAID", "root@10.0.0.2")
SSH_KEY = os.path.expanduser(os.environ.get("SSH_KEY", "~/.ssh/unraid_ed25519"))
AMP_CONTAINER = os.environ.get("AMP_CONTAINER", "AMP")

STATES = {-1: "Undefined", 0: "Stopped", 5: "PreStart", 7: "Configuring", 10: "Starting", 20: "Ready",
          30: "Restarting", 40: "Stopping", 45: "PreparingForSleep", 50: "Sleeping", 60: "Waiting",
          70: "Installing", 75: "Updating", 80: "AwaitingUserInput", 100: "Failed", 200: "Suspended",
          250: "Maintenance", 999: "Indeterminate"}


def creds():
    if os.environ.get("AMP_USER") and os.environ.get("AMP_PASS"):
        return os.environ["AMP_USER"], os.environ["AMP_PASS"]
    out = subprocess.run(["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", UNRAID,
                          f"docker inspect {AMP_CONTAINER} --format '{{{{range .Config.Env}}}}{{{{println .}}}}{{{{end}}}}'"],
                         capture_output=True, text=True, check=True).stdout
    env = dict(l.split("=", 1) for l in out.splitlines() if l.startswith(("USERNAME=", "PASSWORD=")))
    return env["USERNAME"], env["PASSWORD"]


def call(base, method, sid=None, **params):
    if sid:
        params["SESSIONID"] = sid
    req = urllib.request.Request(f"{base}/{method}", data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    return json.loads(body) if body.strip() else None


def login(base, user, pw):
    r = call(base, "Core/Login", username=user, password=pw, token="", rememberMe=False)
    if not r or not r.get("success"):
        raise SystemExit(f"AMP login failed at {base}: {r and r.get('resultReason')}")
    return r["sessionID"]


class Instance:
    def __init__(self, name):
        self.user, self.pw = creds()
        self.ads_base = f"{AMP_URL}/API"
        self.ads = login(self.ads_base, self.user, self.pw)
        inst = [i for i in self.local_instances() if i["InstanceName"] == name]
        if not inst:
            raise SystemExit(f"no AMP instance named {name!r}")
        self.name, self.id = name, inst[0]["InstanceID"]
        self.base = f"{AMP_URL}/API/ADSModule/Servers/{self.id}/API"
        self.sid = None

    def local_instances(self):
        return call(self.ads_base, "ADSModule/GetLocalInstances", self.ads)

    def connect(self):
        """Make sure the instance process is up and log in to it through the ADS proxy."""
        if self.sid:
            return
        call(self.ads_base, "ADSModule/StartInstance", self.ads, InstanceName=self.name)
        for _ in range(40):
            try:
                self.sid = login(self.base, self.user, self.pw)
                call(self.base, "Core/GetUpdates", self.sid)  # drain console backlog
                return
            except (SystemExit, OSError):
                time.sleep(3)
        raise SystemExit(f"instance {self.name} API never came up")

    def api(self, method, **params):
        self.connect()
        return call(self.base, method, self.sid, **params)

    def state(self):
        return self.api("Core/GetStatus")["State"]

    def wait(self, done, fail=(100,), timeout=600, echo=True):
        deadline, last = time.time() + timeout, None
        while time.time() < deadline:
            upd = self.api("Core/GetUpdates")
            if echo:
                for e in upd.get("ConsoleEntries", []):
                    print(f"  | {e.get('Contents')}"[:200], flush=True)
            st = upd.get("Status", {}).get("State")
            if st != last:
                print(f"== {self.name}: {STATES.get(st, st)}", flush=True)
                last = st
            if st in done:
                return st
            if st in fail:
                raise SystemExit(f"{self.name} entered {STATES.get(st, st)}")
            time.sleep(2)
        raise SystemExit(f"timed out waiting for {self.name} ({STATES.get(last, last)})")

    def get(self, node):
        r = self.api("Core/GetConfig", node=node)
        if not isinstance(r, dict) or "CurrentValue" not in r:
            raise SystemExit(f"GetConfig {node} failed: {r}")
        return r["CurrentValue"]

    def set(self, node, value):
        value = str(value)
        r = self.api("Core/SetConfig", node=node, value=value)
        if r and r.get("Status") is False and "provisioning" in (r.get("Reason") or ""):
            # Ports etc. belong to the instance's provisioning spec: only the ADS controller may change
            # them. That reloads the instance and invalidates our session, so reconnect afterwards
            # (otherwise later SetConfig calls fail silently against a dead session).
            r = call(self.ads_base, "ADSModule/SetInstanceConfig", self.ads,
                     InstanceName=self.name, SettingNode=node, Value=value)
            self.sid = None
            time.sleep(5)
        if r and r.get("Status") is False:
            raise SystemExit(f"SetConfig {node}={value} refused: {r.get('Reason')}")
        # Read back: AMP can accept a call and still not apply it.
        got = self.get(node)
        if str(got).strip().lower() != value.strip().lower():
            raise SystemExit(f"SetConfig {node}: wrote {value!r} but AMP reports {got!r}")


def wait_task_quiet(inst, settle=5, timeout=900):
    """AMP's updater runs as a background task while the app stays Stopped; wait for tasks to clear."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        tasks = [t for t in (inst.api("Core/GetTasks") or []) if not t.get("EndTime")]
        if not tasks:
            time.sleep(settle)
            if not [t for t in (inst.api("Core/GetTasks") or []) if not t.get("EndTime")]:
                return
        else:
            print("  .. " + "; ".join(f"{t.get('Name')} {t.get('ProgressPercent')}%" for t in tasks), flush=True)
        time.sleep(5)
    raise SystemExit("timed out waiting for AMP background tasks")


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    cmd, name, rest = argv[0], argv[1], argv[2:]

    if cmd == "create":
        friendly, web_port = rest[0], int(rest[1])
        user, pw = creds()
        ads_base = f"{AMP_URL}/API"
        ads = login(ads_base, user, pw)
        if any(i["InstanceName"] == name for i in call(ads_base, "ADSModule/GetLocalInstances", ads)):
            print(f"{name} already exists; nothing to do")
            return
        # Host it on this controller (the ADS's own target entry) in the default datastore (id 1).
        target = call(ads_base, "ADSModule/GetInstances", ads, ForceIncludeSelf=True)[0]["InstanceId"]
        r = call(ads_base, "ADSModule/CreateInstance", ads, TargetADSInstance=target,
                 NewInstanceId=str(uuid.uuid4()), Module="Minecraft", InstanceName=name, FriendlyName=friendly,
                 IPBinding="0.0.0.0", PortNumber=web_port, AdminUsername=user, AdminPassword=pw,
                 ProvisionSettings={}, AutoConfigure=True, PostCreate=0, StartOnBoot=False,
                 DisplayImageSource="", TargetDatastore=1, Group="")
        print("CreateInstance:", r)
        if not r or r.get("Status") is False:
            raise SystemExit(1)
        return

    inst = Instance(name)
    if cmd == "status":
        print(STATES.get(inst.state(), inst.state()))
    elif cmd == "stop":
        if inst.state() != 0:
            inst.api("Core/Stop")
            inst.wait({0}, timeout=180, echo=False)
        print(f"{name}: Stopped")
    elif cmd == "start":
        inst.api("Core/Start")
        time.sleep(3)
        inst.wait({20}, timeout=int(os.environ.get("START_TIMEOUT", "600")))
    elif cmd == "neoforge":
        version = rest[0]
        changed = False
        if str(inst.get("MinecraftModule.Minecraft.ServerType")) != "51":
            inst.set("MinecraftModule.Minecraft.ServerType", "51"); changed = True
        if inst.get("MinecraftModule.Minecraft.SpecificNeoForgeVersion") != version:
            inst.set("MinecraftModule.Minecraft.SpecificNeoForgeVersion", version); changed = True
        if inst.get("MinecraftModule.Minecraft.ServerJAR") != "[Autoselect]":
            inst.set("MinecraftModule.Minecraft.ServerJAR", "[Autoselect]")
        if changed or "--force" in rest:
            if inst.state() != 0:
                raise SystemExit("stop the app before changing NeoForge")
            print(f"installing NeoForge {version} via AMP updater...")
            inst.api("Core/UpdateApplication")
            time.sleep(3)
            wait_task_quiet(inst)
        print(f"{name}: NeoForge {inst.get('MinecraftModule.Minecraft.SpecificNeoForgeVersion')} "
              f"(server jar {inst.get('MinecraftModule.Minecraft.ServerJAR')})")
    elif cmd == "settings":
        settings = json.load(open(rest[0]))
        for node, value in settings.items():
            if node.startswith("_"):
                continue
            inst.set(node, value)
            print(f"  set {node} = {value}")
    elif cmd == "autostart":
        on = rest[0] == "on"
        r = call(inst.ads_base, "ADSModule/UpdateInstanceInfo", inst.ads, InstanceId=inst.id, FriendlyName=None,
                 Description=None, StartOnBoot=on, Suspended=None, ExcludeFromFirewall=None, RunInContainer=None,
                 ContainerMemory=None, ContainerSwap=None, MemoryPolicy=None, ContainerMaxCPU=None,
                 ContainerCPUSet=None, ContainerImage=None, WelcomeMessage=None, DisplayGroup=None,
                 CustomMountBindings=None, ExtraContainerPackages=None, IsMultiIPAware=None,
                 UseHostModeNetwork=None, SaveOnly=True)
        inst.set("Core.AMP.AppStartupMode", "2" if on else "0")  # enum: 0 Do Nothing, 2 Start
        print(f"{name}: autostart {'on' if on else 'off'} ({r})")
    elif cmd == "schedule":
        # Nightly 04:30 (container TZ, America/Detroit): stop -> backup -> start. The stop/start
        # doubles as the daily restart. Idempotent: matched by description.
        desc = "create-pack: nightly backup + restart (04:30)"
        sd = inst.api("Core/GetScheduleData")
        trig = next((t for t in sd.get("PopulatedTriggers", []) if t.get("Description") == desc), None)
        if not trig:
            inst.api("Core/AddIntervalTrigger", months=list(range(1, 13)), days=list(range(0, 7)), hours=[4],
                     minutes=[30], daysOfMonth=list(range(1, 32)), description=desc)
            sd = inst.api("Core/GetScheduleData")
            trig = next(t for t in sd["PopulatedTriggers"] if t.get("Description") == desc)
        if not any(t.get("TaskMethodName") == "Event.LocalFileBackupPlugin.TakeBackup" for t in trig.get("Tasks", [])):
            inst.api("Core/AddTask", TriggerID=trig["Id"], MethodID="Event.LocalFileBackupPlugin.TakeBackup",
                     ParameterMapping={"Local": "true", "S3": "false", "Sticky": "false", "DirtyOnly": "false",
                                       "BackupWhileRunning": "false", "RestartEvenIfNotRunning": "false"})
        inst.api("Core/SetTriggerEnabled", Id=trig["Id"], Enabled=True)
        trig = next(t for t in inst.api("Core/GetScheduleData")["PopulatedTriggers"] if t["Id"] == trig["Id"])
        print(f"{name}: '{desc}' enabled={trig.get('EnabledState')} tasks="
              f"{[t.get('TaskMethodName') for t in trig.get('Tasks', [])]}")
    elif cmd == "console":
        inst.api("Core/SendConsoleMessage", message=" ".join(rest))
        time.sleep(3)
        for e in inst.api("Core/GetUpdates").get("ConsoleEntries", []):
            print(f"  | {e.get('Contents')}"[:200])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
