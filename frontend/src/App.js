import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import axios from "axios";
import "@/App.css";

// Pages
import QuotesList from "@/components/QuotesList";
import QuoteForm from "@/components/QuoteForm";
import QuoteView from "@/components/QuoteView";
import CompanySettings from "@/components/CompanySettings";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [quotes, setQuotes] = useState([]);
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    // تحقق من تسجيل الدخول سابقاً
    const savedLogin = localStorage.getItem("loggedIn");
    if (savedLogin === "true") {
      setLoggedIn(true);
    }
    fetchQuotes();
    fetchCompanyInfo();
  }, []);

  const fetchQuotes = async () => {
    try {
      const response = await axios.get(`${API}/quotes`);
      setQuotes(response.data);
    } catch (error) {
      console.error("Error fetching quotes:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyInfo = async () => {
    try {
      const response = await axios.get(`${API}/company`);
      setCompany(response.data);
    } catch (error) {
      console.error("Error fetching company info:", error);
    }
  };

  const handleLogin = (e) => {
    e.preventDefault();
    // بيانات تسجيل الدخول الصحيحة
    const validUsers = [
      { username: "admin", password: "1234" },
    ];

    const found = validUsers.find(
      (u) => u.username === username && u.password === password
    );

    if (found) {
      setLoggedIn(true);
      localStorage.setItem("loggedIn", "true");
    } else {
      alert("اسم المستخدم أو كلمة المرور غير صحيحة");
    }
  };

  const handleLogout = () => {
    setLoggedIn(false);
    localStorage.removeItem("loggedIn");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!loggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50" dir="rtl">
        <form
          onSubmit={handleLogin}
          className="bg-white shadow-lg rounded-2xl p-8 w-full max-w-sm border"
        >
          <h2 className="text-2xl font-bold text-center mb-6 text-blue-700">تسجيل الدخول</h2>
          <div className="mb-4">
            <label className="block text-right text-gray-700 mb-2">اسم المستخدم</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-2 border rounded-lg text-right"
              placeholder="ادخل اسم المستخدم"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-right text-gray-700 mb-2">كلمة المرور</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border rounded-lg text-right"
              placeholder="ادخل كلمة المرور"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
          >
            دخول
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="App min-h-screen bg-gradient-to-br from-slate-50 to-blue-50" dir="rtl">
      <BrowserRouter>
        <div className="p-4 text-left">
          <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-3 py-1 rounded-lg hover:bg-red-600 transition"
          >
            تسجيل خروج
          </button>
        </div>
        <Routes>
          <Route
            path="/"
            element={
              <QuotesList
                quotes={quotes}
                onQuotesChange={fetchQuotes}
                company={company}
              />
            }
          />
          <Route
            path="/new"
            element={<QuoteForm onSuccess={fetchQuotes} company={company} />}
          />
          <Route
            path="/edit/:id"
            element={<QuoteForm onSuccess={fetchQuotes} company={company} />}
          />
          <Route path="/view/:id" element={<QuoteView company={company} />} />
          <Route
            path="/settings"
            element={
              <CompanySettings
                company={company}
                onCompanyUpdate={fetchCompanyInfo}
              />
            }
          />
        </Routes>
        <Toaster />
      </BrowserRouter>
    </div>
  );
}

export default App;
