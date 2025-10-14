import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowRight, 
  Save, 
  Upload,
  Building2,
  Image
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CompanySettings({ company, onCompanyUpdate }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    name_ar: company?.name_ar || "شركة مثلث الأنظمة المميزة للمقاولات",
    name_en: company?.name_en || "MUTHALLATH AL-ANZIMAH AL-MUMAYYIZAH CONTRACTING CO.",
    description_ar: company?.description_ar || "تصميم وتصنيع وتوريد وتركيب مظلات الشد الإنشائي والخيام والسواتر",
    description_en: company?.description_en || "Design, Manufacture, Supply & Installation of Structure Tension Awnings, Tents & Canopies",
    tax_number: company?.tax_number || "311104439400003",
    street: company?.street || "شارع حائل",
    neighborhood: company?.neighborhood || "حي البغدادية الغربية",
    country: company?.country || "السعودية",
    city: company?.city || "جدة",
    commercial_registration: company?.commercial_registration || "4030255240",
    building: company?.building || "8376",
    postal_code: company?.postal_code || "22231",
    additional_number: company?.additional_number || "3842",
    email: company?.email || "info@tsscoksa.com",
    phone1: company?.phone1 || "+966 50 061 2006",
    phone2: company?.phone2 || "055 538 9792",
    phone3: company?.phone3 || "+966 50 336 5527",
    logo_path: company?.logo_path || null
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error("يجب اختيار ملف صورة صحيح");
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("حجم الملف يجب أن يكون أقل من 5 ميجابايت");
      return;
    }

    try {
      setUploading(true);
      
      const uploadFormData = new FormData();
      uploadFormData.append('file', file);

      const response = await axios.post(`${API}/company/logo`, uploadFormData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setFormData(prev => ({
        ...prev,
        logo_path: response.data.logo_path
      }));

      toast.success("تم رفع الشعار بنجاح");
    } catch (error) {
      toast.error("حدث خطأ أثناء رفع الشعار");
      console.error("Error uploading logo:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      await axios.put(`${API}/company`, formData);
      
      toast.success("تم حفظ معلومات الشركة بنجاح");
      onCompanyUpdate();
      navigate("/");
    } catch (error) {
      toast.error("حدث خطأ أثناء حفظ معلومات الشركة");
      console.error("Error saving company info:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-4"
          data-testid="back-button"
        >
          <ArrowRight className="h-4 w-4 ml-2" />
          العودة إلى القائمة
        </Button>
        
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Building2 className="h-8 w-8 ml-3" />
          إعدادات الشركة
        </h1>
        <p className="text-gray-600 mt-2">
          قم بتحديث معلومات شركتك التي ستظهر في عروض الأسعار
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        
        {/* Logo Section */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Image className="h-5 w-5 ml-2" />
              شعار الشركة
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {formData.logo_path && (
              <div className="flex justify-center">
                <img 
                  src={`${BACKEND_URL}${formData.logo_path}`}
                  alt="شعار الشركة"
                  className="h-32 w-32 object-contain border rounded-lg bg-white p-2"
                  data-testid="company-logo"
                />
              </div>
            )}
            
            <div className="flex justify-center">
              <div className="relative">
                <input
                  type="file"
                  id="logo-upload"
                  accept="image/*"
                  onChange={handleLogoUpload}
                  className="hidden"
                  data-testid="logo-upload-input"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => document.getElementById('logo-upload').click()}
                  disabled={uploading}
                  data-testid="logo-upload-button"
                >
                  {uploading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 ml-2"></div>
                  ) : (
                    <Upload className="h-4 w-4 ml-2" />
                  )}
                  {formData.logo_path ? "تغيير الشعار" : "رفع شعار الشركة"}
                </Button>
              </div>
            </div>
            
            <p className="text-xs text-gray-500 text-center">
              أقصى حجم للملف: 5 ميجابايت. الصيغ المدعومة: JPG, PNG, GIF
            </p>
          </CardContent>
        </Card>

        {/* Company Names */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle>اسم الشركة</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name-ar">اسم الشركة بالعربية</Label>
              <Input
                id="name-ar"
                value={formData.name_ar}
                onChange={(e) => handleInputChange('name_ar', e.target.value)}
                placeholder="اسم الشركة بالعربية"
                data-testid="company-name-ar-input"
              />
            </div>
            
            <div>
              <Label htmlFor="name-en">اسم الشركة بالإنجليزية</Label>
              <Input
                id="name-en"
                value={formData.name_en}
                onChange={(e) => handleInputChange('name_en', e.target.value)}
                placeholder="Company Name in English"
                data-testid="company-name-en-input"
              />
            </div>
            
            <div>
              <Label htmlFor="description-ar">وصف النشاط بالعربية</Label>
              <Input
                id="description-ar"
                value={formData.description_ar}
                onChange={(e) => handleInputChange('description_ar', e.target.value)}
                placeholder="وصف نشاط الشركة بالعربية"
                data-testid="company-description-ar-input"
              />
            </div>
            
            <div>
              <Label htmlFor="description-en">وصف النشاط بالإنجليزية</Label>
              <Input
                id="description-en"
                value={formData.description_en}
                onChange={(e) => handleInputChange('description_en', e.target.value)}
                placeholder="Company Activity Description in English"
                data-testid="company-description-en-input"
              />
            </div>
          </CardContent>
        </Card>

        {/* Legal Information */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle>المعلومات القانونية</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="tax-number">الرقم الضريبي</Label>
              <Input
                id="tax-number"
                value={formData.tax_number}
                onChange={(e) => handleInputChange('tax_number', e.target.value)}
                placeholder="الرقم الضريبي"
                data-testid="tax-number-input"
              />
            </div>
            
            <div>
              <Label htmlFor="commercial-registration">السجل التجاري</Label>
              <Input
                id="commercial-registration"
                value={formData.commercial_registration}
                onChange={(e) => handleInputChange('commercial_registration', e.target.value)}
                placeholder="رقم السجل التجاري"
                data-testid="commercial-registration-input"
              />
            </div>
          </CardContent>
        </Card>

        {/* Address Information */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle>معلومات العنوان</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="street">الشارع</Label>
              <Input
                id="street"
                value={formData.street}
                onChange={(e) => handleInputChange('street', e.target.value)}
                placeholder="اسم الشارع"
                data-testid="street-input"
              />
            </div>
            
            <div>
              <Label htmlFor="neighborhood">الحي</Label>
              <Input
                id="neighborhood"
                value={formData.neighborhood}
                onChange={(e) => handleInputChange('neighborhood', e.target.value)}
                placeholder="اسم الحي"
                data-testid="neighborhood-input"
              />
            </div>
            
            <div>
              <Label htmlFor="city">المدينة</Label>
              <Input
                id="city"
                value={formData.city}
                onChange={(e) => handleInputChange('city', e.target.value)}
                placeholder="اسم المدينة"
                data-testid="city-input"
              />
            </div>
            
            <div>
              <Label htmlFor="country">الدولة</Label>
              <Input
                id="country"
                value={formData.country}
                onChange={(e) => handleInputChange('country', e.target.value)}
                placeholder="اسم الدولة"
                data-testid="country-input"
              />
            </div>
            
            <div>
              <Label htmlFor="building">المبنى</Label>
              <Input
                id="building"
                value={formData.building}
                onChange={(e) => handleInputChange('building', e.target.value)}
                placeholder="رقم المبنى"
                data-testid="building-input"
              />
            </div>
            
            <div>
              <Label htmlFor="postal-code">الرمز البريدي</Label>
              <Input
                id="postal-code"
                value={formData.postal_code}
                onChange={(e) => handleInputChange('postal_code', e.target.value)}
                placeholder="الرمز البريدي"
                data-testid="postal-code-input"
              />
            </div>
            
            <div className="md:col-span-2">
              <Label htmlFor="additional-number">الرقم الإضافي</Label>
              <Input
                id="additional-number"
                value={formData.additional_number}
                onChange={(e) => handleInputChange('additional_number', e.target.value)}
                placeholder="الرقم الإضافي"
                data-testid="additional-number-input"
              />
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
          <CardHeader>
            <CardTitle> الحكام وا الشروط</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Label htmlFor="email">البريد الإلكتروني</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="البريد الإلكتروني"
                data-testid="email-input"
              />
            </div>
            
            <div>
              <Label htmlFor="phone1">رقم الجوال الأول</Label>
              <Input
                id="phone1"
                value={formData.phone1}
                onChange={(e) => handleInputChange('phone1', e.target.value)}
                placeholder="رقم الجوال الأول"
                data-testid="phone1-input"
              />
            </div>
            
            <div>
              <Label htmlFor="phone2">رقم الجوال الثاني</Label>
              <Input
                id="phone2"
                value={formData.phone2}
                onChange={(e) => handleInputChange('phone2', e.target.value)}
                placeholder="رقم الجوال الثاني (اختياري)"
                data-testid="phone2-input"
              />
            </div>
            
            <div className="md:col-span-2">
              <Label htmlFor="phone3">رقم الجوال الإضافي</Label>
              <Input
                id="phone3"
                value={formData.phone3}
                onChange={(e) => handleInputChange('phone3', e.target.value)}
                placeholder="رقم الجوال الإضافي (اختياري)"
                data-testid="phone3-input"
              />
            </div>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4 space-x-reverse">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/")}
            data-testid="cancel-settings-button"
          >
            إلغاء
          </Button>
          <Button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
            data-testid="save-settings-button"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
            ) : (
              <Save className="h-4 w-4 ml-2" />
            )}
            حفظ الإعدادات
          </Button>
        </div>
      </form>
    </div>
  );
}