import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Committee, Andou, Light, Donation

def index(request):
    # 1. 處理年份篩選 (預設取資料庫最新年份，若無則預設乙巳年)
    all_years = list(Committee.objects.values_list('year', flat=True).distinct()) + \
                list(Andou.objects.values_list('year', flat=True).distinct())
    all_years = sorted(list(set(all_years)), reverse=True)
    
    selected_year = request.GET.get('year')
    if not selected_year and all_years:
        selected_year = all_years[0]
    elif not selected_year:
        selected_year = "乙巳年"

    context = {
        'selected_year': selected_year,
        'all_years': all_years,
        'committees': Committee.objects.filter(year=selected_year),
        'andous': Andou.objects.filter(year=selected_year),
        'lights': Light.objects.filter(year=selected_year),
        'donations': Donation.objects.filter(year=selected_year),
    }
    return render(request, 'core/index.html', context)

@login_required
def upload_excel(request, mode):
    """通用上傳邏輯：支援 委員、安斗、點燈、捐獻"""
    if request.method == "POST" and request.FILES.get('excel_file'):
        try:
            df = pd.read_excel(request.FILES['excel_file'])
            # 確保欄位中的空值會被轉為空字串，避免寫入資料庫時報錯
            df = df.fillna('') 

            for _, row in df.iterrows():
                if mode == 'committee':
                    Committee.objects.create(
                        year=str(row['年份']).strip(),
                        title=str(row['職稱']).strip(),
                        name=str(row['姓名']).strip()
                    )
                elif mode == 'andou':
                    Andou.objects.create(
                        year=str(row['年份']).strip(),
                        item=str(row['項目']).strip(),
                        name=str(row['姓名']).strip(),
                        address=str(row.get('地址', '')).strip(),
                        payment_status=(str(row.get('繳費狀態', '')) == '已繳'),
                        remark=str(row.get('備註', '')).strip()
                    )
                elif mode == 'light':  # <--- 修正這段：處理點燈名單
                    Light.objects.create(
                        year=str(row['年份']).strip(),
                        item=str(row['項目']).strip(),
                        name=str(row['姓名']).strip(),
                        payment_status=(str(row.get('繳費狀態', '')) == '已繳'),
                        remark=str(row.get('備註', '')).strip()
                    )
                elif mode == 'donation': # <--- 處理捐獻名單
                    Donation.objects.create(
                        year=str(row['年份']).strip(),
                        name=str(row['姓名']).strip(),
                        amount=int(row['金額'])
                    )
            return redirect('index')
        except Exception as e:
            return HttpResponse(f"上傳出錯了！請檢查 Excel 欄位名稱是否正確。錯誤訊息: {e}")
    
    return render(request, 'core/upload.html', {'mode': mode})

def andou_pdf(request, year):
    # PDF 匯出邏輯 (簡化版)
    from reportlab.pdfgen import canvas
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="andou_{year}.pdf"'
    
    p = canvas.Canvas(response)
    p.setFontSize(16)
    p.drawString(100, 800, f"福明宮 {year} 安斗名單")
    
    y = 750
    for obj in Andou.objects.filter(year=year):
        p.setFontSize(12)
        p.drawString(100, y, f"{obj.item} - {obj.name} - {obj.address}")
        y -= 25
        if y < 50: p.showPage(); y = 800
        
    p.showPage()
    p.save()
    return response

from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Committee, Andou, Light, Donation
from .forms import CommitteeForm, AndouForm, LightForm, DonationForm
from django.views.decorators.http import require_POST

def get_form_content(request):
    mode = request.GET.get('mode')
    pk = request.GET.get('pk')
    instance = None
    
    # 修正點：確保 pk 不是空字串或 None 字符串才查詢
    if pk and pk.strip() and pk != 'None':
        model_map = {'committee': Committee, 'andou': Andou, 'light': Light, 'donation': Donation}
        instance = model_map[mode].objects.get(pk=pk)

    forms_map = {
        'committee': CommitteeForm(instance=instance),
        'andou': AndouForm(instance=instance),
        'light': LightForm(instance=instance),
        'donation': DonationForm(instance=instance),
    }
    form = forms_map.get(mode)
    html = render_to_string('core/partial_form.html', {'form': form}, request=request)
    return JsonResponse({'html': html})

def save_data(request):
    if request.method == "POST":
        mode = request.POST.get('mode')
        pk = request.POST.get('pk')
        instance = None
        
        try:
            # 修正點：pk 為空時視為新增，不執行 get
            if pk and pk.strip() and pk != 'None':
                model_map = {'committee': Committee, 'andou': Andou, 'light': Light, 'donation': Donation}
                instance = model_map[mode].objects.get(pk=pk)
            
            data = request.POST.copy()
            # 處理布林值勾選
            data['payment_status'] = 'payment_status' in data

            form_class_map = {'committee': CommitteeForm, 'andou': AndouForm, 'light': LightForm, 'donation': DonationForm}
            form = form_class_map[mode](data, instance=instance)
            
            if form.is_valid():
                form.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'msg': form.errors.as_text()})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'error', 'msg': '無效請求'})

@require_POST
def delete_data(request):
    mode = request.POST.get('mode')
    pk = request.POST.get('pk')
    try:
        model_map = {
            'committee': Committee, 
            'andou': Andou, 
            'light': Light, 
            'donation': Donation
        }
        if pk and mode in model_map:
            instance = model_map[mode].objects.get(pk=pk)
            instance.delete()
            return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'error', 'msg': '刪除失敗：無效請求'})


import pandas as pd
from django.http import HttpResponse, JsonResponse
from .models import Committee, Andou, Light, Donation
# ... 保留原本的 import ...

@login_required
def export_excel(request, mode):
    """批次匯出 Excel 邏輯"""
    year = request.GET.get('year', '乙巳年')
    
    # 根據模式抓取資料與定義欄位
    if mode == 'committee':
        queryset = Committee.objects.filter(year=year)
        data = list(queryset.values('year', 'title', 'name'))
        columns = ['年份', '職稱', '姓名']
    elif mode == 'andou':
        queryset = Andou.objects.filter(year=year)
        data = list(queryset.values('year', 'item', 'name', 'address', 'payment_status'))
        columns = ['年份', '項目', '姓名', '地址', '繳費狀態']
    elif mode == 'light':
        queryset = Light.objects.filter(year=year)
        data = list(queryset.values('year', 'item', 'name', 'payment_status'))
        columns = ['年份', '項目', '姓名', '繳費狀態']
    elif mode == 'donation':
        queryset = Donation.objects.filter(year=year)
        data = list(queryset.values('year', 'name', 'amount'))
        columns = ['年份', '姓名', '金額']
    else:
        return HttpResponse("無效的模式")

    df = pd.DataFrame(data)
    # 處理布林值轉中文
    if 'payment_status' in df.columns:
        df['payment_status'] = df['payment_status'].map({True: '已繳', False: '未繳'})
    
    # 重新命名欄位（對應 Excel 表頭）
    column_map = dict(zip(['year', 'title', 'name', 'item', 'address', 'payment_status', 'remark', 'amount'], 
                          ['年份', '職稱', '姓名', '項目', '地址', '繳費狀態', '備註', '金額']))
    df.rename(columns=column_map, inplace=True)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{mode}_{year}.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='名單')
    
    return response

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import os
from django.conf import settings

def andou_pdf(request, year):
    # 1. 字體設定 (請確認伺服器路徑正確)
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "msjh.ttc")
    if not os.path.exists(font_path):
        return HttpResponse("找不到系統字體，請檢查路徑。")
    pdfmetrics.registerFont(TTFont('MSJH', font_path))

    # 2. 設定 Response
    response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = f'attachment; filename="安斗名單_{year}.pdf"'

    filename = f"andou_list_{year}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # --- 3. 空間配置 (延長方框至 400 單位) ---
    label_w = 185  # 寬度稍微加寬
    label_h = 800  # 延長方框高度，減少底部空白
    
    x_margin = 20  
    y_margin = 20  # 縮小邊距
    curr_x = x_margin
    curr_y = height - y_margin - label_h

    # 從資料庫抓取資料
    # 注意：請確保 Andou 模型已在此檔案上方 import
    for obj in Andou.objects.filter(year=year):
        # 繪製淺灰色裁切框
        p.setDash(1, 2)
        p.setStrokeColorRGB(0.7, 0.7, 0.7)
        p.rect(curr_x, curr_y, label_w, label_h)
        p.setStrokeColorRGB(0, 0, 0)
        p.setDash() # 恢復實線
        
        # --- 4. 姓名邏輯 (保留頓號、延遲換行、字體加大) ---
        raw_name = obj.name.replace(" ", "").strip()
        name_len = len(raw_name)
        
        # 根據總字數決定字體大小與「每欄換行字數上限」
        if name_len > 40:
            name_size, step_y, limit = 26, 28, 28 # 極長姓名
        elif name_len > 18:
            name_size, step_y, limit = 30, 32, 24 # 中長名單
        else:
            name_size, step_y, limit = 36, 38, 24  # 少數人，字體極大

        p.setFont('MSJH', name_size)
        start_y = curr_y + label_h - 35 # 統一從頂部往下 35 單位開始寫

        if name_len <= limit:
            # 單欄：靠右側居中
            draw_x = curr_x + (label_w * 0.75)
            draw_y = start_y
            for char in raw_name:
                p.drawCentredString(draw_x, draw_y, char)
                draw_y -= step_y
        else:
            # 雙欄：第一欄填滿 limit 個字後才換到第二欄
            col1 = raw_name[:limit]
            col2 = raw_name[limit:]
            
            # 第一排 (最右側)
            x1 = curr_x + (label_w * 0.85)
            y1 = start_y
            for char in col1:
                p.drawCentredString(x1, y1, char)
                y1 -= step_y
                
            # 第二排 (往左移)
            x2 = curr_x + (label_w * 0.60)
            y2 = start_y
            for char in col2:
                p.drawCentredString(x2, y2, char)
                y2 -= step_y

        # --- 5. 地址邏輯 (符號轉向、字體放大) ---
        p.setFont('MSJH', 26)
        # 處理直式橫槓：將 - 替換為 ｜
        addr_text = f"住址：{obj.address}".replace("-", "｜").replace("－", "｜")
        
        addr_x = curr_x + (label_w * 0.28)
        addr_y = start_y
        
        for char in addr_text:
            if addr_y < curr_y + 15: # 到底部安全線就停止，防止溢出
                break 
            p.drawCentredString(addr_x, addr_y, char)
            addr_y -= 30 # 地址行距

        # --- 6. 換格與自動分頁 ---
        curr_x += label_w + 10 # 欄與欄間距
        
        # 如果右邊放不下，換到下一橫列
        if curr_x + label_w > width:
            curr_x = x_margin
            curr_y -= (label_h + 10) # 兩列之間的間距
        
        # 如果下方放不下，開新頁面
        if curr_y < 20:
            p.showPage()
            curr_x = x_margin
            curr_y = height - y_margin - label_h

    p.showPage()
    p.save()
    return response