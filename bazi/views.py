from django.shortcuts import render
from .forms import BirthTimeForm


def bazi_view(request):
    if request.method == 'POST':
        form = BirthTimeForm(request.POST)
        if form.is_valid():
            # Handle the valid form data here
            pass
    else:
        form = BirthTimeForm()

    return render(request, 'bazi.html', {'form': form})
