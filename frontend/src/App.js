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

  useEffect(() => {
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="App min-h-screen bg-gradient-to-br from-slate-50 to-blue-50" dir="rtl">
      <BrowserRouter>
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
