from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from app.routers.tasks_osb import all_task
from app.routers.result_tasks import result_by_id_day, monitor, result_good, result_bad, result_id_day_monitor

router = APIRouter(prefix='/pages', tags=['Фронтенд'])
templates = Jinja2Templates(directory='app/templates')


@router.get('/all_tasks')
async def get_all_task_html(request: Request, all_tasks=Depends(all_task)):
    return templates.TemplateResponse(name='all_tasks.html',
                                      context={'request': request, 'all_tasks': all_tasks})


@router.get('/result_id_day_monitor')
async def get_result_id_day_monitor_html(request: Request, result_id_day_monitor=Depends(result_id_day_monitor)):
    return templates.TemplateResponse(name='result_id_day_monitor.html',
                                      context={'request': request, 'result_id_day_monitor': result_id_day_monitor})

@router.get('/result_id_day_monitor/pasha')
async def get_result_id_day_monitor_html_pasha(request: Request, result_id_day_monitor=Depends(result_id_day_monitor)):
    return templates.TemplateResponse(name='result_id_day_monitor_pasha.html',
                                      context={'request': request, 'result_id_day_monitor': result_id_day_monitor})

@router.get('/monitor')
async def get_result_by_id_day_html(request: Request, monitor=Depends(monitor),result_by_id_day=Depends(result_by_id_day), result_good=Depends(result_good), result_bad=Depends(result_bad)):
    return templates.TemplateResponse(name='monitor.html',
                                      context={'request': request, 'monitor': monitor, 'result_by_id_day': result_by_id_day, 'result_good': result_good, 'result_bad': result_bad})