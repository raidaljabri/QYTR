import React, { useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import html2pdf from "html2pdf.js";

const QuoteView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const pdfRef = useRef();

  // دالة تصدير PDF
  const handleExport = () => {
    const element = pdfRef.current;
    const opt = {
      margin: [16, 16, 16, 16], // هوامش من الأعلى والأسفل واليمين واليسار (مم)
      filename: `Quote_${id}.pdf`,
      image: { type: "jpeg", quality: 1 },
      html2canvas: {
        scale: 2, // جودة عالية
        useCORS: true,
      },
      jsPDF: {
        unit: "mm",
        format: "a4",
        orientation: "portrait",
      },
      pagebreak: {
        mode: ["avoid-all", "css", "legacy"],
        before: "#pageBreak",
        after: "#pageBreak",
        avoid: ["tr", "td", "thead"],
      },
    };

    // إضافة مسافة بين الصفحات (10مم)
    const spacer = document.createElement("div");
    spacer.style.height = "10mm";
    spacer.style.pageBreakAfter = "always";
    element.appendChild(spacer);

    html2pdf()
      .set(opt)
      .from(element)
      .save()
      .then(() => {
        spacer.remove(); // إزالة الفاصل بعد التصدير
      });
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">عرض السعر #{id}</h1>
        <div className="space-x-2">
          <Button onClick={() => navigate(-1)} variant="outline">
            رجوع
          </Button>
          <Button onClick={handleExport}>تصدير PDF</Button>
        </div>
      </div>

      <div
        ref={pdfRef}
        className="bg-white p-8 rounded-xl shadow-sm space-y-6"
        style={{
          fontFamily: "Arial, sans-serif",
          lineHeight: 1.5,
          color: "#000",
        }}
      >
        {/* محتوى الصفحة */}
        <div className="text-center border-b pb-4">
          <h2 className="text-xl font-semibold">شركة المثال</h2>
          <p>عرض سعر رسمي</p>
        </div>

        {/* جدول الأسعار كمثال */}
        <table className="w-full border mt-4 text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2">#</th>
              <th className="border p-2">الوصف</th>
              <th className="border p-2">الكمية</th>
              <th className="border p-2">السعر</th>
              <th className="border p-2">الإجمالي</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 25 }).map((_, i) => (
              <tr key={i}>
                <td className="border p-2 text-center">{i + 1}</td>
                <td className="border p-2">منتج رقم {i + 1}</td>
                <td className="border p-2 text-center">1</td>
                <td className="border p-2 text-center">100 ريال</td>
                <td className="border p-2 text-center">100 ريال</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* قسم الأحكام والشروط */}
        <div id="pageBreak" className="mt-6">
          <h3 className="text-lg font-semibold mb-2">الأحكام والشروط</h3>
          <p>
            هذا النص مثال للأحكام والشروط الخاصة بعرض السعر. سيتم تقسيم النص
            تلقائيًا عبر الصفحات في حالة زيادته عن حجم الصفحة. كما تم إضافة
            مسافة مقدارها 10مم بين كل صفحة وأخرى داخل ملف الـ PDF النهائي.
          </p>
        </div>
      </div>
    </div>
  );
};

export default QuoteView;
