import { useState, useEffect } from "react";
import { api, post, patch, resetCsrf } from "./api";

function Card({ title, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [login, setLogin] = useState({ email: "", password: "" });
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [history, setHistory] = useState([]);
  const [today, setToday] = useState(null);
  const [leaves, setLeaves] = useState([]);
  const [stats, setStats] = useState(null);
  const [report, setReport] = useState(null);
  const [newDept, setNewDept] = useState("");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [employeeForm, setEmployeeForm] = useState({
    code: "",
    name: "",
    email: "",
    password: "",
    department_id: "",
    designation: "",
    base_salary: "0",
  });
  const [leaveForm, setLeaveForm] = useState({
    leave_type: "Casual",
    start_date: "",
    end_date: "",
    reason: "",
  });
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));

  async function load(role = user?.role) {
    if (!role) return;
    if (role === "admin") {
      const [dep, emp, lr, dashboard, monthly] = await Promise.all([
        api("/departments"),
        api("/employees"),
        api("/leaves"),
        api("/dashboard"),
        api(`/reports/monthly?month=${month}`),
      ]);
      setDepartments(dep);
      setEmployees(emp);
      setLeaves(lr);
      setStats(dashboard);
      setReport(monthly);
    } else {
      const [day, hist, lr] = await Promise.all([
        api("/attendance/today"),
        api("/attendance/history"),
        api("/leaves"),
      ]);
      setToday(day);
      setHistory(hist);
      setLeaves(lr);
    }
  }

  useEffect(() => {
    api("/auth/me")
      .then(async (account) => {
        setUser(account);
        await load(account.role);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function act(callback, success = "Saved") {
    setError("");
    setNotice("");
    try {
      await callback();
      setNotice(success);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function loginSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      const account = await post("/auth/login", login);
      setUser(account);
      setLogin({ email: "", password: "" });
      await load(account.role);
    } catch (e) {
      setError(e.message);
    }
  }

  async function signOut() {
    setError("");
    try {
      await post("/auth/logout");
      await resetCsrf();
      setUser(null);
      setNotice("");
      setStats(null);
      setReport(null);
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading) return <main>Loading...</main>;

  if (!user) {
    return (
      <main className="login">
        <Card title="Employee Attendance System">
          <form onSubmit={loginSubmit}>
            <label>
              Email
              <input
                type="email"
                value={login.email}
                required
                onChange={(e) => setLogin({ ...login, email: e.target.value })}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={login.password}
                required
                onChange={(e) => setLogin({ ...login, password: e.target.value })}
              />
            </label>
            <button type="submit">Sign in</button>
          </form>
          {error && <p className="error">{error}</p>}
        </Card>
      </main>
    );
  }

   return (
    <main>
      <header>
        <h1>Employee Attendance System</h1>
        <span>
          {user.email} ({user.role})
        </span>
        <button onClick={signOut}>Log out</button>
      </header>

      {error && <p className="error">{error}</p>}
      {notice && <p className="success">{notice}</p>}

      {user.role === "admin" ? (
        <>
          <Card title="Today's attendance overview">
            <div className="stats">
              {Object.entries(stats || {}).map(([key, val]) => (
                <div key={key}>
                  <strong>{val}</strong>
                  <small>{key.replace("_", " ")}</small>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Add department">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                act(async () => {
                  await post("/departments", { name: newDept });
                  setNewDept("");
                }, "Department added");
              }}
            >
              <input
                placeholder="Department name"
                value={newDept}
                required
                onChange={(e) => setNewDept(e.target.value)}
              />
              <button>Add</button>
            </form>
            <p>{departments.map((d) => d.name).join(", ") || "No departments yet"}</p>
          </Card>

          <Card title="Register employee">
            <form
              className="grid"
              onSubmit={(e) => {
                e.preventDefault();
                act(async () => {
                  await post("/employees", employeeForm);
                  setEmployeeForm({
                    code: "",
                    name: "",
                    email: "",
                    password: "",
                    department_id: "",
                    designation: "",
                    base_salary: "0",
                  });
                }, "Employee registered");
              }}
            >
              {["code", "name", "email", "password", "designation", "base_salary"].map((k) => (
                <label key={k}>
                  {k.replace("_", " ")}
                  <input
                    value={employeeForm[k]}
                    required
                    type={k === "password" ? "password" : k === "email" ? "email" : k === "base_salary" ? "number" : "text"}
                    min={k === "base_salary" ? 0 : undefined}
                    onChange={(e) => setEmployeeForm({ ...employeeForm, [k]: e.target.value })}
                  />
                </label>
              ))}
              <label>
                Department
                <select
                  required
                  value={employeeForm.department_id}
                  onChange={(e) => setEmployeeForm({ ...employeeForm, department_id: e.target.value })}
                >
                  <option value="">Select department</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
              <button>Register</button>
            </form>
          </Card>

          <Card title="Employees">
            <input
              placeholder="Search employee"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button
              type="button"
              onClick={async () => {
                try {
                  setEmployees(await api(`/employees?search=${encodeURIComponent(search)}`));
                } catch (e) {
                  setError(e.message);
                }
              }}
            >
              Search
            </button>
            <button
              type="button"
              onClick={() => {
                setSearch("");
                load();
              }}
            >
              Show all
            </button>

            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Designation</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((e) => (
                    <tr key={e.id}>
                      <td>{e.code}</td>
                      <td>{e.name}</td>
                      <td>{e.designation}</td>
                      <td>{e.active ? "Active" : "Inactive"}</td>
                      <td>
                        <button onClick={() => setEditing({ ...e })}>Edit</button>
                        <button
                          onClick={() =>
                            act(
                              () => patch(`/employees/${e.id}/status`, { active: !e.active }),
                              "Status updated"
                            )
                          }
                        >
                          {e.active ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {editing && (
            <Card title={`Edit ${editing.code}`}>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  act(async () => {
                    await patch(`/employees/${editing.id}`, {
                      name: editing.name,
                      designation: editing.designation,
                      department_id: editing.department_id,
                      base_salary: editing.base_salary,
                    });
                    setEditing(null);
                  }, "Employee updated");
                }}
              >
                {["name", "designation", "base_salary"].map((key) => (
                  <label key={key}>
                    {key}
                    <input
                      required
                      value={editing[key]}
                      onChange={(e) => setEditing({ ...editing, [key]: e.target.value })}
                    />
                  </label>
                ))}
                <label>
                  Department
                  <select
                    value={editing.department_id}
                    onChange={(e) => setEditing({ ...editing, department_id: e.target.value })}
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button>Save</button>
                <button type="button" onClick={() => setEditing(null)}>
                  Cancel
                </button>
              </form>
            </Card>
          )}

          <Card title="Review leave requests">
            {leaves.map((l) => (
              <div className="row" key={l.id}>
                Employee #{l.employee_id} — {l.leave_type} — {l.start_date} to {l.end_date} — {l.reason} — <strong>{l.status}</strong>
                {l.status === "pending" && (
                  <>
                    <button
                      onClick={() =>
                        act(() => patch(`/leaves/${l.id}/decision`, { status: "approved" }), "Leave approved")
                      }
                    >
                      Approve
                    </button>
                    <button
                      onClick={() =>
                        act(() => patch(`/leaves/${l.id}/decision`, { status: "rejected" }), "Leave rejected")
                      }
                    >
                      Reject
                    </button>
                  </>
                )}
              </div>
            ))}
          </Card>

          <Card title="Monthly attendance / illustrative salary summary">
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
            <button
              onClick={() =>
                act(() => api(`/reports/monthly?month=${month}`).then(setReport), "Report updated")
              }
            >
              Load month
            </button>
            <p>{report?.note}</p>
            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Present days</th>
                    <th>Late days</th>
                    <th>Work minutes</th>
                    <th>Estimate</th>
                  </tr>
                </thead>
                <tbody>
                  {(report?.employees || []).map((e) => (
                    <tr key={e.employee_code}>
                      <td>{e.name}</td>
                      <td>{e.present_days}</td>
                      <td>{e.late_days}</td>
                      <td>{e.work_minutes}</td>
                      <td>{e.attendance_based_estimate}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      ) : (
        <>
          <Card title="Today's attendance">
            <p>
              {today
                ? `${today.status} | Check-in: ${today.check_in} | Check-out: ${today.check_out ?? "Not yet"}`
                : "Not checked in"}
            </p>
            <button
              disabled={!!today}
              onClick={() => act(() => post("/attendance/check-in"), "Check-in recorded")}
            >
              Check in
            </button>
            <button
              disabled={!today || !!today.check_out}
              onClick={() => act(() => post("/attendance/check-out"), "Check-out recorded")}
            >
              Check out
            </button>
          </Card>

          <Card title="My attendance history">
            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th>Work minutes</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id}>
                      <td>{h.date}</td>
                      <td>{h.check_in}</td>
                      <td>{h.check_out ?? "—"}</td>
                      <td>{h.work_minutes}</td>
                      <td>{h.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Request leave">
            <form
              className="grid"
              onSubmit={(e) => {
                e.preventDefault();
                act(async () => {
                  await post("/leaves", leaveForm);
                  setLeaveForm({
                    leave_type: "Casual",
                    start_date: "",
                    end_date: "",
                    reason: "",
                  });
                }, "Leave request submitted");
              }}
            >
              {["leave_type", "start_date", "end_date", "reason"].map((k) => (
                <label key={k}>
                  {k.replace("_", " ")}
                  <input
                    required
                    value={leaveForm[k]}
                    type={k.endsWith("date") ? "date" : "text"}
                    onChange={(e) => setLeaveForm({ ...leaveForm, [k]: e.target.value })}
                  />
                </label>
              ))}
              <button>Submit request</button>
            </form>
            {leaves.map((l) => (
              <p key={l.id}>
                {l.start_date} to {l.end_date}: <strong>{l.status}</strong>
              </p>
            ))}
          </Card>
        </>
      )}
    </main>
  );
}