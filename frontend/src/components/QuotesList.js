import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Plus, 
  FileText, 
  Settings, 
  Trash2, 
  Edit, 
  Eye,
  Download,
  FileSpreadsheet,
  Building2
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function QuotesList({ quotes, onQuotesChange, company }) {
  const navigate = useNavigate();

  const handleDelete = async (quoteId) => {
    try {
      await axios.delete(`${API}/quotes/${quoteId}`);
      toast.success("تم حذف عرض السعر بنجاح");
      onQuotesChange();
    } catch (error) {
      toast.error("حدث خطأ أثناء حذف عرض السعر");
      console.error("Error deleting quote:", error);
    }
  };

  const handleExport = async (quoteId, format) => {
    try {
      const response = await axios.get(`${API}/quotes/${quoteId}/export/${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const extension = format === 'excel' ? 'xlsx' : 'pdf';
      link.setAttribute('download', `quote_${quoteId}.${extension}`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`تم تحميل عرض السعر كـ ${format === 'excel' ? 'Excel' : 'PDF'}`);
    } catch (error) {
      toast.error("حدث خطأ أثناء تحميل الملف");
      console.error("Error exporting quote:", error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4 space-x-reverse">
            {company?.logo_path && (
              <img 
                src={`${BACKEND_URL}${company.logo_path}`}
                alt="شعار الشركة"
                className="h-16 w-16 object-contain"
              />
            )}
            <div>
              <h1 className="text-4xl font-bold text-gray-900 font-['Playfair_Display']">
                {company?.name_ar || "شركة مثلث الأنظمة المميزة للمقاولات"}
              </h1>
              <p className="text-lg text-gray-600 mt-2">
                {company?.description_ar}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {company?.name_en}
              </p>
            </div>
          </div>
          <div className="flex space-x-3 space-x-reverse">
            <Button
              onClick={() => navigate("/settings")}
              variant="outline"
              size="lg"
              className="flex items-center space-x-2 space-x-reverse"
              data-testid="settings-button"
            >
              <Settings className="h-5 w-5" />
              <span>الإعدادات</span>
            </Button>
            <Button
              onClick={() => navigate("/new")}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 space-x-reverse"
              data-testid="new-quote-button"
            >
              <Plus className="h-5 w-5" />
              <span>عرض سعر جديد</span>
            </Button>
          </div>
        </div>

        <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-6 border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 numbers-en" data-testid="total-quotes">
                {quotes.length}
              </div>
              <div className="text-gray-600">إجمالي عروض الأسعار</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 numbers-en" data-testid="total-value">
                {quotes.reduce((sum, quote) => sum + (quote.total_amount || 0), 0).toLocaleString('en-US')}
              </div>
              <div className="text-gray-600">إجمالي القيمة (ريال)</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600" data-testid="this-month">
                {quotes.filter(quote => {
                  const quoteDate = new Date(quote.created_date);
                  const now = new Date();
                  return quoteDate.getMonth() === now.getMonth() && 
                         quoteDate.getFullYear() === now.getFullYear();
                }).length}
              </div>
              <div className="text-gray-600">هذا الشهر</div>
            </div>
          </div>
        </div>
      </div>

      {/* Quotes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {quotes.map((quote) => (
          <Card 
            key={quote.id} 
            className="hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-white/80 backdrop-blur-sm border-0 shadow-lg"
            data-testid={`quote-card-${quote.id}`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <Badge variant="secondary" className="text-sm">
                  رقم {quote.quote_number}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {formatDate(quote.created_date)}
                </Badge>
              </div>
              <CardTitle className="text-xl text-right">
                {quote.customer.name}
              </CardTitle>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <div className="text-right">
                <p className="text-sm text-gray-600 mb-1">وصف المشروع:</p>
                <p className="text-gray-800 line-clamp-2">
                  {quote.project_description}
                </p>
              </div>
              
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">الموقع:</span>
                <span className="text-gray-800">{quote.location}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">المبلغ الإجمالي:</span>
                <span className="text-lg font-bold text-green-600">
                  {quote.total_amount.toLocaleString('ar-SA')} ريال
                </span>
              </div>
              
              <div className="flex items-center justify-between pt-4 border-t">
                <div className="flex space-x-2 space-x-reverse">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/view/${quote.id}`)}
                    data-testid={`view-quote-${quote.id}`}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/edit/${quote.id}`)}
                    data-testid={`edit-quote-${quote.id}`}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        data-testid={`delete-quote-${quote.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>تأكيد الحذف</AlertDialogTitle>
                        <AlertDialogDescription>
                          هل أنت متأكد من حذف عرض السعر رقم {quote.quote_number}؟
                          هذا الإجراء لا يمكن التراجع عنه.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>إلغاء</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDelete(quote.id)}
                          className="bg-red-600 hover:bg-red-700"
                        >
                          حذف
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
                
                <div className="flex space-x-1 space-x-reverse">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(quote.id, 'pdf')}
                    data-testid={`export-pdf-${quote.id}`}
                  >
                    <FileText className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExport(quote.id, 'excel')}
                    data-testid={`export-excel-${quote.id}`}
                  >
                    <FileSpreadsheet className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {/* Empty state */}
        {quotes.length === 0 && (
          <div className="col-span-full">
            <Card className="bg-white/50 backdrop-blur-sm border-dashed border-2 border-gray-300">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Building2 className="h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">
                  لا توجد عروض أسعار بعد
                </h3>
                <p className="text-gray-500 mb-6 text-center">
                  ابدأ بإنشاء أول عرض سعر لشركتك
                </p>
                <Button
                  onClick={() => navigate("/new")}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                  data-testid="first-quote-button"
                >
                  <Plus className="h-5 w-5 mr-2" />
                  إنشاء عرض سعر جديد
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}