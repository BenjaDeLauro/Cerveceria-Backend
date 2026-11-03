from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto


class BienvenidaView(TemplateView):
    template_name = 'inicio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos_recientes'] = Producto.objects.select_related(
            'categoria', 'marca', 'presentacion',
        ).order_by('-pk')[:3]
        context['total_productos'] = Producto.objects.count()
        context['total_categorias'] = Categoria.objects.count()
        return context


class ProductoListView(ListView):
    template_name = 'catalogo/productos.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        productos = Producto.objects.select_related('categoria', 'marca', 'presentacion')
        busqueda = self.request.GET.get('q', '').strip()
        if busqueda:
            productos = productos.filter(Q(nombre__icontains=busqueda)
                                         | Q(descripcion__icontains=busqueda))
        return productos.order_by('nombre', 'pk')


class GestionCatalogoMixin(LoginRequiredMixin, PermissionRequiredMixin):
    template_name = 'catalogo/formulario.html'


class ProductoCreateView(GestionCatalogoMixin, SuccessMessageMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    permission_required = 'catalogo.add_producto'
    success_url = reverse_lazy('catalogo_web:productos')
    success_message = 'Producto creado correctamente.'
    extra_context = {'titulo': 'Agregar producto', 'volver': 'catalogo_web:productos'}


class ProductoUpdateView(GestionCatalogoMixin, SuccessMessageMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    permission_required = 'catalogo.change_producto'
    success_url = reverse_lazy('catalogo_web:productos')
    success_message = 'Producto actualizado correctamente.'
    extra_context = {'titulo': 'Editar producto', 'volver': 'catalogo_web:productos'}


class EliminacionProtegidaMixin:
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            form.add_error(None, 'No se puede eliminar: hay registros asociados. Revisalos desde el administrador.')
            return self.form_invalid(form)


class ProductoDeleteView(GestionCatalogoMixin, EliminacionProtegidaMixin,
                         SuccessMessageMixin, DeleteView):
    model = Producto
    template_name = 'catalogo/eliminar.html'
    permission_required = 'catalogo.delete_producto'
    success_url = reverse_lazy('catalogo_web:productos')
    success_message = 'Producto eliminado correctamente.'
    extra_context = {'titulo': 'Eliminar producto', 'volver': 'catalogo_web:productos'}


class CategoriaListView(GestionCatalogoMixin, ListView):
    model = Categoria
    template_name = 'catalogo/categorias.html'
    context_object_name = 'categorias'
    permission_required = 'catalogo.view_categoria'
    ordering = ('nombre', 'pk')
    paginate_by = 20


class CategoriaCreateView(GestionCatalogoMixin, SuccessMessageMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    permission_required = 'catalogo.add_categoria'
    success_url = reverse_lazy('catalogo_web:categorias')
    success_message = 'Categoría creada correctamente.'
    extra_context = {'titulo': 'Agregar categoría', 'volver': 'catalogo_web:categorias'}


class CategoriaUpdateView(GestionCatalogoMixin, SuccessMessageMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    permission_required = 'catalogo.change_categoria'
    success_url = reverse_lazy('catalogo_web:categorias')
    success_message = 'Categoría actualizada correctamente.'
    extra_context = {'titulo': 'Editar categoría', 'volver': 'catalogo_web:categorias'}


class CategoriaDeleteView(GestionCatalogoMixin, EliminacionProtegidaMixin,
                          SuccessMessageMixin, DeleteView):
    model = Categoria
    template_name = 'catalogo/eliminar.html'
    permission_required = 'catalogo.delete_categoria'
    success_url = reverse_lazy('catalogo_web:categorias')
    success_message = 'Categoría eliminada correctamente.'
    extra_context = {'titulo': 'Eliminar categoría', 'volver': 'catalogo_web:categorias'}
