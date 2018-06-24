using System.ComponentModel;

namespace MotionPic.ViewModel
{
    public class MainGenericVM : NotifyPropertyChangedBase, INotifyPropertyChanged
    {
        public MainGenericVM()
        {
            aViewModel = new MotionPicViewModel();
            aux1VM = new SimpleMotionPicViewModel();
            aux2VM = new SimpleMotionPicViewModel();
        }
        private MotionPicViewModel _aViewModel = null;
        public MotionPicViewModel aViewModel
        {
            get
            {
                if (_aViewModel == null)
                    _aViewModel = new MotionPicViewModel();
                return _aViewModel;
            }
            set
            {
                if (_aViewModel != value)
                {
                    _aViewModel = value;
                    _aViewModel.VidSourceCollection = new ObservableVidSource();
                    OnPropertyChanged();
                }
            }
        }
        private SimpleMotionPicViewModel _aux1VM;
        public SimpleMotionPicViewModel aux1VM
        {
            get
            {
                if (_aux1VM == null)
                    _aux1VM = new SimpleMotionPicViewModel();
                return _aux1VM;
            }
            set
            {
                if (_aux1VM != value)
                {
                    _aux1VM = value;
                    _aux1VM.VidSourceCollection = new ObservableVidSource();
                    OnPropertyChanged();
                }
            }
        }
        private SimpleMotionPicViewModel _aux2VM;
        public SimpleMotionPicViewModel aux2VM
        {
            get
            {
                if (_aux2VM == null)
                    _aux2VM = new SimpleMotionPicViewModel();
                return _aux2VM;
            }
            set
            {
                if (_aux2VM != value)
                {
                    _aux2VM = value;
                    _aux2VM.VidSourceCollection = new ObservableVidSource();
                    OnPropertyChanged();
                }
            }
        }
    }
}
