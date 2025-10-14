import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { toast } from "sonner";
import { useReactToPrint } from "react-to-print";
import {
  ArrowRight,
  Edit,
  FileText,
  FileSpreadsheet,
  Printer,
} from "lucide-react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function QuoteView({ company }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const printRef = useRef();

  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuote();
  }, [id]);

  const fetchQuote = async () => {
    try {
      const response = await axios.get(`${API}/quotes/${id}`);
      setQuote(response.data);
    } catch (error) {
      toast.error("حدث خطأ أثناء تحميل عرض السعر");
      console.error("Error fetching quote:", error);
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = useReactToPrint({
    content: () => printRef.current,
    documentTitle: `Quote_${quote?.quote_number}`,
  });

  const handleExport = () => {
    if (!printRef.current) return;
    const input = printRef.current;

    html2canvas(input, { scale: 2 }).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");

      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save(`Quote_${quote.quote_number}.pdf`);
      toast.success("تم تحميل عرض السعر كـ PDF");
    }).catch((error) => {
      toast.error("حدث خطأ أثناء إنشاء PDF");
      console.error("Error creating PDF:", error);
    });
  };

  const formatHijriDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("ar-SA", {
      year: "numeric",
      month: "long",
      day: "numeric",
      calendar: "islamic",
    });
  };

  const formatGregorianDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>عرض السعر غير موجود</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* شريط الأزرار */}
      <div className="mb-6 flex items-center justify-between print:hidden">
        <Button variant="ghost" onClick={() => navigate("/")}>
          <ArrowRight className="h-4 w-4 ml-2" />
          العودة إلى القائمة
        </Button>

        <div className="flex space-x-3 space-x-reverse">
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="h-4 w-4 ml-2" />
          </Button>

          <Button variant="outline" onClick={handleExport}> 
            <FileText className="h-4 w-4 ml-2" /> تحميل PDF
          </Button>

          <Button variant="outline" onClick={() => {
            axios.get(`${API}/quotes/${id}/export/excel`, { responseType: "blob" })
              .then((response) => {
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement("a");
                link.href = url;
                link.setAttribute("download", `quote_${quote.quote_number}.xlsx`);
                document.body.appendChild(link);
                link.click();
                link.remove();
                toast.success("تم تحميل عرض السعر كـ Excel");
              })
              .catch((error) => {
                toast.error("حدث خطأ أثناء تحميل الملف");
                console.error("Error exporting Excel:", error);
              });
          }}>
            <FileSpreadsheet className="h-4 w-4 ml-2" />
            تحميل Excel
          </Button>

          <Button
            onClick={() => navigate(`/edit/${quote.id}`)}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Edit className="h-4 w-4 ml-2" />
            تعديل
          </Button>
        </div>
      </div>

      {/* المحتوى القابل للطباعة */}
      <div
        ref={printRef}
        className="bg-white p-8 shadow-lg rounded-lg print:shadow-none print:rounded-none"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-8 border-b pb-6">
          <div className="flex items-center space-x-4 space-x-reverse">
            {company?.logo_path && (
              <img
                src={`${BACKEND_URL}${company.logo_path}`}
                alt="شعار الشركة"
                className="h-20 w-20 object-contain"
              />
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {company?.name_ar || "شركة مثلث الأنظمة المميزة للمقاولات"}
              </h1>
              <p className="text-gray-600 mt-1">{company?.description_ar}</p>
              <p className="text-sm text-gray-500 mt-1">{company?.name_en}</p>
            </div>
          </div>

          <div className="text-right">
            <Badge variant="secondary" className="text-lg px-4 py-2 mb-4">
              عرض سعر رقم QYT26- {quote.quote_number}
            </Badge>
            <div className="text-sm text-gray-600 space-y-1">
              <p>
                <strong>التاريخ:</strong> {formatHijriDate(quote.created_date)} / {formatGregorianDate(quote.created_date)}
              </p>
            </div>
          </div>
        </div>

        {/* معلومات الشركة والعميل */}
        <div className="grid grid-cols-2 gap-8 mb-8">
          <div>
            <h3 className="text-lg font-semibold mb-3 text-blue-600">
              المورد / Seller
            </h3>
            <div className="text-sm space-y-1">
              <p><strong>الشركة:</strong> {company?.name_ar}</p>
              <p><strong>الرقم الضريبي:</strong> {company?.tax_number}</p>
              <p><strong>المدينة:</strong> {company?.city}</p>
              <p><strong>الدولة:</strong> {company?.country}</p>
              <p><strong>السجل التجاري:</strong> {company?.commercial_registration}</p>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-3 text-green-600">
              العميل / Customer
            </h3>
            <div className="text-sm space-y-1">
              <p><strong>العميل:</strong> {quote.customer.name}</p>
              {quote.customer.tax_number && (
                <p><strong>الرقم الضريبي:</strong> {quote.customer.tax_number}</p>
              )}
              {quote.customer.city && (
                <p><strong>المدينة:</strong> {quote.customer.city}</p>
              )}
              {quote.customer.phone && (
                <p><strong>رقم الهاتف:</strong> {quote.customer.phone}</p>
              )}
            </div>
          </div>
        </div>

        {/* تفاصيل المشروع */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3 text-purple-600">
            تفاصيل المشروع / Project details
          </h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="font-medium">{quote.project_description}</p>
            {quote.location && (
              <p className="font-medium mt-2">الموقع: {quote.location}</p>
            )}
          </div>
        </div>

        {/* جدول الأسعار */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3">جدول الأسعار / Price table</h3>
          <div className="overflow-x-auto">
            <table className="w-full border border-gray-300">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-3 py-2 text-center text-sm font-medium">الرقم</th>
                  <th className="border px-3 py-2 text-right text-sm font-medium">الوصف</th>
                  <th className="border px-3 py-2 text-center text-sm font-medium">الكمية</th>
                  <th className="border px-3 py-2 text-center text-sm font-medium">الوحدة</th>
                  <th className="border px-3 py-2 text-center text-sm font-medium">سعر الوحدة</th>
                  <th className="border px-3 py-2 text-center text-sm font-medium">السعر الإجمالي</th>
                </tr>
              </thead>
              <tbody>
                {quote.items.map((item, i) => (
                  <tr key={i}>
                    <td className="border px-3 py-2 text-center text-sm">{i + 1}</td>
                    <td className="border px-3 py-2 text-right text-sm">{item.description}</td>
                    <td className="border px-3 py-2 text-center text-sm">{item.quantity}</td>
                    <td className="border px-3 py-2 text-center text-sm">{item.unit}</td>
                    <td className="border px-3 py-2 text-center text-sm">{item.unit_price.toLocaleString("en-US",{ minimumFractionDigits:2, maximumFractionDigits:2 })}</td>
                    <td className="border px-3 py-2 text-center text-sm font-medium">{item.total_price.toLocaleString("en-US",{ minimumFractionDigits:2, maximumFractionDigits:2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* الإجماليات */}
        <div className="flex justify-end mb-8">
          <div className="w-80 space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span>المجموع الفرعي:</span>
              <span className="font-medium">{quote.subtotal.toLocaleString("en-US",{ minimumFractionDigits:2, maximumFractionDigits:2 })} ريال</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span>الضريبة (15%):</span>
              <span className="font-medium">{quote.tax_amount.toLocaleString("en-US",{ minimumFractionDigits:2, maximumFractionDigits:2 })} ريال</span>
            </div>
            <div className="flex justify-between py-3 text-lg font-bold text-green-600 border-t-2 border-gray-400">
              <span>الإجمالي:</span>
              <span>{quote.total_amount.toLocaleString("en-US",{ minimumFractionDigits:2, maximumFractionDigits:2 })} ريال</span>
            </div>
          </div>
        </div>

        {/* الأحكام والشروط */}
        {quote.notes && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-3">الأحكام والشروط / Terms and conditions</h3>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm whitespace-pre-wrap break-words" dir="auto" style={{ textAlign:'start' }}>
                {quote.notes}
              </p>
            </div>
          </div>
        )}

        {/* معلومات التواصل */}
        <div className="border-t pt-6 mt-8 text-center text-sm text-gray-600 space-y-1">
          <p><strong>معلومات الاتصال / Contact information</strong></p>
          <p>البريد الإلكتروني: {company?.email}</p>
          <p>{company?.neighborhood}, {company?.city}</p>
          <div className="flex justify-center space-x-4 space-x-reverse">
            <p>جوال: {company?.phone1}</p>
            {company?.phone2 && <p>جوال آخر: {company?.phone2}</p>}
            {company?.phone3 && <p>جوال إضافي: {company?.phone3}</p>}
          </div>
        </div>

        {/* التوقيع */}
        <div className="mt-12 pt-8 border-t">
          <div className="grid grid-cols-2 gap-8">
            <div className="text-center">
              <div className="border-t border-gray-400 pt-2 mt-16">
                <p className="text-sm text-gray-600">التوقيع والختم</p>
              </div>
            </div>
            <div className="text-center">
              <div className="border-t border-gray-400 pt-2 mt-16">
                <p className="text-sm text-gray-600">توقيع العميل</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
