using AForge.Video;
using AForge.Video.DirectShow;
using System.Drawing;
using System.Windows.Media.Imaging;
using System.Linq;
using System.ComponentModel;
using System;
using System.IO;
using System.Drawing.Imaging;
using System.Windows.Input;
using System.Windows;
using System.Windows.Threading;
using System.Diagnostics;
using MotionPic.ViewModel;

namespace MotionPic
{
    public class SimpleMotionPicViewModel : NotifyPropertyChangedBase, INotifyPropertyChanged
    {
       
        private static bool InvokeRequired
        {
            get { return Dispatcher.CurrentDispatcher != Application.Current.Dispatcher; }
        }

        #region ICommand implementation
        private ICommand theCommandRunCamera;
        public ICommand CommandRunCamrera
        {
            get
            {
                if (null == theCommandRunCamera)
                {
                    theCommandRunCamera = new RelayCommand(
                         param => ToggleRunCameraSource((bool)param),
                         param => CanRunCommand((bool)param)
                        );
                }
                return theCommandRunCamera;
            }
        }
        #endregion
        #region Camera Commands
        private void ToggleRunCameraSource(bool IsCheckedParam)
        {
            if (IsCheckedParam)
            {
                if (CanExecRunCameraSource) //just make sure, is checked previously by CanRunCommand
                {
                    if (StartCameraSource())
                    {
                        IsReadonlyCameraSource = true;
                    }
                }
            }
            else
            {
                if (StopCameraSource())
                {
                    IsReadonlyCameraSource = false;
                }
            }
        }
        private bool CanRunCommand(bool IsCheckedParam)
        {
            if (IsCheckedParam)
            {
                return true; //it not checked therfore running, can always stop
            }
            else
            {
                return CanExecRunCameraSource;
            }
            return true; //the usual should-not-happen; check if so why
        }
        private bool CanExecRunCameraSource
        {
            get { return IsNotRunningVideoSource; }
        }
        private bool CanExecStopCameraSource
        {
            get { return IsRunningVideoSource; }
        }
        private bool CanExecDisposeCameraSource
        {
            get { return !IsRunningVideoSource; }
        }
        private bool CanExecSwitchCameraSource
        {
            get { return IsNullVideoSource; }
        }
        private bool IsNotRunningVideoSource
        {
            get { return !IsNullVideoSource && !CurrentVideoCaptureDevice.IsRunning; }
        }
        private bool IsRunningVideoSource
        {
            get { return !IsNullVideoSource && CurrentVideoCaptureDevice.IsRunning; }
        }
        private bool IsNullVideoSource
        {
            get { return (null == CurrentVideoCaptureDevice); }
        }

        private bool SelectValidCameraSource()
        {
            if (CanExecSwitchCameraSource)
            {
                CurrentVideoCaptureDevice = CreateCaptureVideoSource(SelectedVidSource());
                CurrentVideoCaptureDevice.NewFrame += new NewFrameEventHandler(video_frame_wpf_bitmapimage);
                return true;
            }
            else
            {
                throw new InvalidOperationException("called on non-null prior source");
            }
            return false;
        }
        private bool DisposeCameraSource()
        {
            if (CanExecDisposeCameraSource)
            {
                CurrentVideoCaptureDevice = null;
                return true;
            }
            return false;
        }
        private bool TryForceSetupValidCameraSource()
        {
            if (!CanExecSwitchCameraSource)
            {
                if (CanExecStopCameraSource)
                {
                    if (!StopCameraSource()) return false;
                }
                if (CanExecDisposeCameraSource)
                {
                    if (!DisposeCameraSource()) return false;
                }
            }
            if (CanExecSwitchCameraSource)
            {
                if (SelectValidCameraSource())
                {
                    VidCapCollection.SyncCaps(CurrentVideoCaptureDevice.VideoCapabilities);
                    return true;
                }
            }
            return false;
        }
        private bool StartCameraSource()
        {
            if (CanExecRunCameraSource)
            {
                CurrentVideoCaptureDevice.Start();
                return true;
            }
            return false;
        }
        private bool StopCameraSource()
        {
            if (CanExecStopCameraSource)
            {
                // remove new frame handler??
                CurrentVideoCaptureDevice.SignalToStop();
                CurrentVideoCaptureDevice.WaitForStop();
                VidWidth = 0;
                VidHeight = 0;
                VidFPS = 0;
                VidBytesRcvd = 0;
                return true;
            }
            return false;
        }
        private bool theValueIsReadonlyCameraSource = false;
        public bool IsReadonlyCameraSource
        {
            get { return theValueIsReadonlyCameraSource; }
            private set
            {
                if (theValueIsReadonlyCameraSource != value)
                {
                    theValueIsReadonlyCameraSource = value;
                    OnPropertyChanged();
                }
            }
        }
        public bool IsReadWriteCameraSource
        {
            get { return !IsReadonlyCameraSource; }
            private set
            {
                if (IsReadonlyCameraSource == value)
                {
                    IsReadonlyCameraSource = !value;
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        #region VideoSources
        private ObservableVidSource theObservableCollection;
        public ObservableVidSource VidSourceCollection
        {
            get { return theObservableCollection; }
            set
            {
                if (theObservableCollection != value)
                {
                    theObservableCollection = value;
                    OnPropertyChanged();
                }
            }
        }
        private int theSelectedVidSourceCollectionIndex = -1;
        public int SelectedVidSourceCollectionIndex
        {
            get { return theSelectedVidSourceCollectionIndex; }
            set
            {
                if (theSelectedVidSourceCollectionIndex != value)
                {
                    theSelectedVidSourceCollectionIndex = value;
                    TryForceSetupValidCameraSource();
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        #region VideoCapabilities
        private VideoCapabilityCollection theObservableVidCaps = new VideoCapabilityCollection();
        public VideoCapabilityCollection VidCapCollection
        {
            get { return theObservableVidCaps; }
            set
            {
                if (theObservableVidCaps != value)
                {
                    theObservableVidCaps = value;
                    OnPropertyChanged();
                }
            }
        }
        private int theSelectedVidCapCollectionIndex;
        public int SelectedVidCapCollectionIndex
        {
            get { return theSelectedVidCapCollectionIndex; }
            set
            {
                if (theSelectedVidCapCollectionIndex != value)
                {
                    theSelectedVidCapCollectionIndex = value;
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        #region The Camera Device
        private FilterInfo SelectedVidSource()
        {
            FilterInfo rv = null;
            if (null != VidSourceCollection.ElementAt(theSelectedVidSourceCollectionIndex))
            {
                rv = VidSourceCollection.ElementAt(theSelectedVidSourceCollectionIndex);
            }
            return rv;
        }
        private VideoCaptureDevice theCurrentVideoCaptureDevice = null;
        private VideoCaptureDevice CurrentVideoCaptureDevice
        {
            get { return theCurrentVideoCaptureDevice; }
            set
            {
                if (theCurrentVideoCaptureDevice != value)
                {
                    theCurrentVideoCaptureDevice = value;
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        private VideoCaptureDevice CreateCaptureVideoSource(FilterInfo selectedVideoSource)
        {
            VideoCaptureDevice rv = null;
            if (null != selectedVideoSource)
            {
                rv = new VideoCaptureDevice(selectedVideoSource.MonikerString);
            }
            VidCapCollection.SyncCaps(rv.VideoCapabilities);
            if (VidCapCollection.Count > 0)
            {
                SelectedVidCapCollectionIndex = 0;
            }
            else
            {
                SelectedVidCapCollectionIndex = -1;
            }
            return rv;
        }
       
        #region ViewModelPropertiesRunningVideo;
        private Rectangle theVideoPixelRectangleInfo = new Rectangle(0, 0, 0, 0);
        public int VidWidth
        {
            get { return theVideoPixelRectangleInfo.Width; }
            set
            {
                if (theVideoPixelRectangleInfo.Width != value)
                {
                    theVideoPixelRectangleInfo.Width = value;
                    OnPropertyChanged();
                }
            }
        }
        public int VidHeight
        {
            get { return theVideoPixelRectangleInfo.Height; }
            set
            {
                if (theVideoPixelRectangleInfo.Height != value)
                {
                    theVideoPixelRectangleInfo.Height = value;
                    OnPropertyChanged();
                }
            }
        }

        private long theVidBytesRcvd;
        public long VidBytesRcvd
        {
            get { return theVidBytesRcvd; }
            private set
            {
                if (theVidBytesRcvd != value)
                {
                    theVidBytesRcvd = value;
                    OnPropertyChanged();
                }
            }
        }

        private double theVidFPS;
        public double VidFPS
        {
            get { return theVidFPS; }
            private set
            {
                if (theVidFPS != value)
                {
                    theVidFPS = value;
                    OnPropertyChanged();
                }
            }
        }

        private BitmapSource theCurrentPicture = null;
        public BitmapSource CurrentPicture
        {
            get
            {
                if (null != theCurrentPicture)
                {
                    return theCurrentPicture;
                }
                return null;
            }
            private set
            {
                if (theCurrentPicture != value)
                {
                    theCurrentPicture = value;
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        #region picture properties
        private void video_frame_wpf_bitmapimage(object sender, NewFrameEventArgs eventArgs)
        {
            //BitmapImage bi = null;
            try
            {
                // get new frame
                using (Bitmap source = eventArgs.Frame.Clone() as Bitmap)
                {
                    Bitmap bitmap = source;
                    VidHeight = bitmap.Height;
                    VidWidth = bitmap.Width;

                    // now manipulate the bitmap as seeing fit


                    //CurrentPicture = CreateBitmapSourceFromBitmap(bitmap);
                    CurrentPicture = (BitmapSource)Application.Current.Dispatcher.Invoke(
                                new Func<Bitmap, BitmapSource>(CreateBitmapSourceFromBitmap),
                                DispatcherPriority.Normal,
                                bitmap
                            );
                }
                VidBytesRcvd = CurrentVideoCaptureDevice.BytesReceived;
                //VidFPS = VidFramesRcvd(CurrentVideoCaptureDevice.FramesReceived);
            }
            catch (Exception ex)
            {
                if (null != ex)
                {

                }
            }
        }
        public static BitmapSource CreateBitmapSourceFromBitmap(Bitmap bitmap)
        {
            if (bitmap == null)
                throw new ArgumentNullException("bitmap");

            if (Application.Current.Dispatcher == null)
                return null; // Is it possible?

            try
            {

                using (MemoryStream memoryStream = new MemoryStream())
                {
                    // You need to specify the image format to fill the stream. 
                    // I'm assuming it is PNG
                    bitmap.Save(memoryStream, ImageFormat.Bmp);
                    memoryStream.Seek(0, SeekOrigin.Begin);

                    // Make sure to create the bitmap in the UI thread
                    if (InvokeRequired)
                        return (BitmapSource)Application.Current.Dispatcher.Invoke(
                                new Func<Stream, BitmapSource>(CreateBitmapSourceFromBitmap),
                                DispatcherPriority.Normal,
                                memoryStream
                            );

                    return CreateBitmapSourceFromBitmap(memoryStream);
                }
            }
            catch (Exception)
            {
                return null;
            }
        }
        private static BitmapSource CreateBitmapSourceFromBitmap(Stream stream)
        {
            BitmapDecoder bitmapDecoder = BitmapDecoder.Create(
                stream,
                BitmapCreateOptions.PreservePixelFormat,
                BitmapCacheOption.OnLoad);

            // This will disconnect the stream from the image completely...
            BitmapSource bi = bitmapDecoder.Frames.Single();

            bi.Freeze();
            return bi;
        }
        #endregion
    }
    public class MotionPicViewModel : NotifyPropertyChangedBase, INotifyPropertyChanged
    {
        private static bool InvokeRequired
        {
            get { return Dispatcher.CurrentDispatcher != Application.Current.Dispatcher; }
        }

        #region ICommand implementation
        private ICommand theCommandRunCamera;
        public ICommand CommandRunCamrera
        {
            get
            {
                if (null == theCommandRunCamera)
                {
                    theCommandRunCamera = new RelayCommand(
                         param => ToggleRunCameraSource((bool)param),
                         param => CanRunCommand((bool)param)
                        );
                }
                return theCommandRunCamera;
            }
        }
        #endregion
        private void ToggleRunCameraSource(bool IsCheckedParam)
        {
            if (IsCheckedParam)
            {
                if (CanExecRunCameraSource) //just make sure, is checked previously by CanRunCommand
                {
                    if (StartCameraSource())
                    {
                        IsReadonlyCameraSource = true;
                    }
                }
            }
            else
            {
                if (StopCameraSource())
                {
                    IsReadonlyCameraSource = false;
                }
            }
        }
        private bool CanRunCommand(bool IsCheckedParam)
        {
            if (IsCheckedParam)
            {
                return true; //it not checked therfore running, can always stop
            }
            else
            {
                return CanExecRunCameraSource;
            }
            return true; //the usual should-not-happen; check if so why
        }
        private bool CanExecRunCameraSource
        {
            get { return IsNotRunningVideoSource; }
        }
        private bool CanExecStopCameraSource
        {
            get { return IsRunningVideoSource; }
        }
        private bool CanExecDisposeCameraSource
        {
            get { return !IsRunningVideoSource; }
        }
        private bool CanExecSwitchCameraSource
        {
            get { return IsNullVideoSource; }
        }
        private bool IsNotRunningVideoSource
        {
            get { return !IsNullVideoSource && !CurrentVideoCaptureDevice.IsRunning; }
        }
        private bool IsRunningVideoSource
        {
            get { return !IsNullVideoSource && CurrentVideoCaptureDevice.IsRunning; }
        }
        private bool IsNullVideoSource
        {
            get { return (null == CurrentVideoCaptureDevice); }
        }

        private bool SelectValidCameraSource() {
            if (CanExecSwitchCameraSource)
            {
                CurrentVideoCaptureDevice = CreateCaptureVideoSource(SelectedVidSource());
                CurrentVideoCaptureDevice.NewFrame += new NewFrameEventHandler(video_frame_wpf_bitmapimage);
                return true;
            }
            else
            {
                throw new InvalidOperationException("called on non-null prior source");
            }
            return false;
        }
        private bool DisposeCameraSource()
        {
            if (CanExecDisposeCameraSource)
            {
                CurrentVideoCaptureDevice = null;
                return true;
            }
            return false;
        }
        private bool TryForceSetupValidCameraSource()
        {
            if (!CanExecSwitchCameraSource)
            {
                if (CanExecStopCameraSource)
                {
                    if (!StopCameraSource()) return false;
                }
                if (CanExecDisposeCameraSource)
                {
                    if (!DisposeCameraSource()) return false;
                }
            }
            if (CanExecSwitchCameraSource)
            {
                if (SelectValidCameraSource())
                {
                    VidCapCollection.SyncCaps(CurrentVideoCaptureDevice.VideoCapabilities);
                    return true;
                }
            }
            return false;
        }
        private bool StartCameraSource()
        {
            if (CanExecRunCameraSource)
            {
                CurrentVideoCaptureDevice.Start();
                return true;
            }
            return false;
        }
        private bool StopCameraSource()
        {
            if (CanExecStopCameraSource)
            {
                // remove new frame handler??
                CurrentVideoCaptureDevice.SignalToStop();
                CurrentVideoCaptureDevice.WaitForStop();
                VidWidth = 0;
                VidHeight = 0;
                VidFPS = 0;
                VidBytesRcvd = 0;
                return true;
            }
            return false;
        }
        private bool theValueIsReadonlyCameraSource = false;
        public bool IsReadonlyCameraSource
        {
            get { return theValueIsReadonlyCameraSource; }
            private set
            {
                if (theValueIsReadonlyCameraSource != value)
                {
                    theValueIsReadonlyCameraSource = value;
                    OnPropertyChanged();
                }
            }
        }
        public bool IsReadWriteCameraSource
        {
            get { return !IsReadonlyCameraSource; }
            private set
            {
                if (IsReadonlyCameraSource == value)
                {
                    IsReadonlyCameraSource = !value;
                    OnPropertyChanged();
                }
            }
        }
        #region VideoSources
        private ObservableVidSource theObservableCollection;
        public ObservableVidSource VidSourceCollection
        {
            get { return theObservableCollection; }
            set
            {
                if (theObservableCollection != value)
                {
                    theObservableCollection = value;
                    OnPropertyChanged();
                }
            }
        }
        private int theSelectedVidSourceCollectionIndex =-1;
        public int SelectedVidSourceCollectionIndex
        {
            get { return theSelectedVidSourceCollectionIndex; }
            set
            {
                if (theSelectedVidSourceCollectionIndex != value)
                {
                    theSelectedVidSourceCollectionIndex = value;
                    TryForceSetupValidCameraSource();
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        #region VideoCapabilities
        private VideoCapabilityCollection theObservableVidCaps = new VideoCapabilityCollection();
        public VideoCapabilityCollection VidCapCollection
        {
            get { return theObservableVidCaps; }
            set
            {
                if (theObservableVidCaps != value)
                {
                    theObservableVidCaps = value;
                    OnPropertyChanged();
                }
            }
        }
        private int theSelectedVidCapCollectionIndex;
        public int SelectedVidCapCollectionIndex
        {
            get { return theSelectedVidCapCollectionIndex; }
            set
            {
                if (theSelectedVidCapCollectionIndex != value)
                {
                    theSelectedVidCapCollectionIndex = value;
                    OnPropertyChanged();
                }
            }
        }
        #endregion
        private FilterInfo SelectedVidSource()
        {
            FilterInfo rv = null;
            if (null != VidSourceCollection.ElementAt(theSelectedVidSourceCollectionIndex))
            {
                rv = VidSourceCollection.ElementAt(theSelectedVidSourceCollectionIndex);
            }
            return rv;
        }

        private VideoCaptureDevice theCurrentVideoCaptureDevice = null;
        private VideoCaptureDevice CurrentVideoCaptureDevice
        {
            get { return theCurrentVideoCaptureDevice; }
            set
            {
                if (theCurrentVideoCaptureDevice!=value)
                {
                    theCurrentVideoCaptureDevice = value;
                    OnPropertyChanged();
                }
            }
        }

        //private AsyncVideoSource CreateAsyncVideoSource(FilterInfo selectedVideoSource)
        //{
        //    AsyncVideoSource rv = null;
        //    if (null != selectedVideoSource)
        //    {
        //        VideoCaptureDevice capture = new VideoCaptureDevice(selectedVideoSource.MonikerString);
        //        rv.SkipFramesIfBusy = true;
        //        rv = new AsyncVideoSource(capture);
        //    }
        //    return rv;
        //}
        private VideoCaptureDevice CreateCaptureVideoSource(FilterInfo selectedVideoSource)
        {
            VideoCaptureDevice rv = null;
            if (null != selectedVideoSource)
            {
                rv = new VideoCaptureDevice(selectedVideoSource.MonikerString);
            }
            VidCapCollection.SyncCaps(rv.VideoCapabilities);
            if (VidCapCollection.Count > 0)
            {
                SelectedVidCapCollectionIndex = 0;
            }
            else
            {
                SelectedVidCapCollectionIndex = -1;
            }
            return rv;
        }
        //public AsyncVideoSource VideoSource
        //{
        //    get { return theAsyncvideoSource;  }
        //    private set { OnPropertyChanged(); }
        //}
        // from my robots code
        //private BitmapSource refreshRenderedBitmaps(double aHeight, double aWidth)
        //{
        //    Size aViewPort = new Size();
        //    aViewPort.Height = Convert.ToInt32(aHeight);
        //    aViewPort.Width = Convert.ToInt32(aWidth);
        //    //aSceneManager.Camera.Viewport = aViewPort;

        //    BitmapSizeOptions aGDISizeOption = BitmapSizeOptions.FromWidthAndHeight(aViewPort.Width, aViewPort.Height);
        //    return System.Windows.Interop.Imaging.CreateBitmapSourceFromHBitmap(aSceneManager.Render.GetHbitmap(), IntPtr.Zero, Int32Rect.Empty, aGDISizeOption);
        //}

        #region ViewModelPropertiesRunningVideo;
        private Rectangle theVideoPixelRectangleInfo = new Rectangle(0, 0, 0, 0);
        public int VidWidth
        {
            get { return theVideoPixelRectangleInfo.Width; }
            set
            {
                if (theVideoPixelRectangleInfo.Width != value)
                {
                    theVideoPixelRectangleInfo.Width = value;
                    OnPropertyChanged();
                }
            }
        }
        public int VidHeight
        {
            get { return theVideoPixelRectangleInfo.Height; }
            set
            {
                if (theVideoPixelRectangleInfo.Height != value)
                {
                    theVideoPixelRectangleInfo.Height = value;
                    OnPropertyChanged();
                }
            }
        }

        private long theVidBytesRcvd;
        public long VidBytesRcvd
        {
            get { return theVidBytesRcvd; }
            private set
            {
                if (theVidBytesRcvd != value)
                {
                    theVidBytesRcvd = value;
                    OnPropertyChanged();
                }
            }
        }

        private double theVidFPS;
        public double VidFPS
        {
            get { return theVidFPS; }
            private set
            {
                if (theVidFPS != value)
                {
                    theVidFPS = value;
                    OnPropertyChanged();
                }
            }
        }
        
        private BitmapSource theCurrentPicture = null;
        public BitmapSource CurrentPicture
        {
            get
            {
                if (null != theCurrentPicture)
                {
                    return theCurrentPicture;
                }
                return null;
            }
            private set
            {
                if (theCurrentPicture != value)
                {
                    theCurrentPicture = value;
                    OnPropertyChanged();
                }
            }
        }

        private double theControlAngle;
        public double ControlAngle
        {
            get { return theControlAngle; }
            set
            {
                if (theControlAngle != value)
                {
                    theControlAngle = value;
                    OnPropertyChanged();
                };
            }
        }
        #endregion

        #region ProcessVideoFrames
        private void video_frame_forms(object sender, NewFrameEventArgs eventArgs)
        {

        }
        private void video_frame_wpf_bitmapimage(object sender, NewFrameEventArgs eventArgs)
        {
            //BitmapImage bi = null;
            try
            {
                // get new frame
                using (Bitmap source = eventArgs.Frame.Clone() as Bitmap)
                {
                    Bitmap bitmap = testcrop(source);
                    VidHeight = bitmap.Height;
                    VidWidth = bitmap.Width;

                    // now manipulate the bitmap as seeing fit


                    //CurrentPicture = CreateBitmapSourceFromBitmap(bitmap);
                    CurrentPicture = (BitmapSource)Application.Current.Dispatcher.Invoke(
                                new Func<Bitmap, BitmapSource>(CreateBitmapSourceFromBitmap),
                                DispatcherPriority.Normal,
                                bitmap
                            );
                }
                VidBytesRcvd = CurrentVideoCaptureDevice.BytesReceived;
                VidFPS = VidFramesRcvd(CurrentVideoCaptureDevice.FramesReceived);
            }
            catch (Exception ex)
            {
                if (null != ex)
                {

                }
            }
        }
        public static BitmapSource CreateBitmapSourceFromBitmap(Bitmap bitmap)
        {
            if (bitmap == null)
                throw new ArgumentNullException("bitmap");

            if (Application.Current.Dispatcher == null)
                return null; // Is it possible?

            try
            {

                using (MemoryStream memoryStream = new MemoryStream())
                {
                    // You need to specify the image format to fill the stream. 
                    // I'm assuming it is PNG
                    bitmap.Save(memoryStream, ImageFormat.Bmp);
                    memoryStream.Seek(0, SeekOrigin.Begin);

                    // Make sure to create the bitmap in the UI thread
                    if (InvokeRequired)
                        return (BitmapSource)Application.Current.Dispatcher.Invoke(
                                new Func<Stream, BitmapSource>(CreateBitmapSourceFromBitmap),
                                DispatcherPriority.Normal,
                                memoryStream
                            );

                    return CreateBitmapSourceFromBitmap(memoryStream);
                }
            }
            catch (Exception)
            {
                return null;
            }
        }
        private static BitmapSource CreateBitmapSourceFromBitmap(Stream stream)
        {
            BitmapDecoder bitmapDecoder = BitmapDecoder.Create(
                stream,
                BitmapCreateOptions.PreservePixelFormat,
                BitmapCacheOption.OnLoad);

            // This will disconnect the stream from the image completely...
            BitmapSource bi = bitmapDecoder.Frames.Single();

            bi.Freeze();
            return bi;
        }
        private static Bitmap testcrop(Bitmap source)
        {
            Bitmap rv = null;
            AForge.Imaging.Filters.Crop theCropFilter;
            if (null != source)
            {
                int smalledgesize = Math.Min(source.Width, source.Height);
                int starthorizontal = (source.Width - smalledgesize) / 2;
                int startvertical = (source.Height - smalledgesize) / 2;
                theCropFilter = new AForge.Imaging.Filters.Crop(new Rectangle(starthorizontal, startvertical, smalledgesize, smalledgesize));
                rv = theCropFilter.Apply(source);
            }
            return rv;
        }
        //private void video_frame_wpf_writeablebitmap(object sender, NewFrameEventArgs eventArgs)
        //{
        //    try
        //    {

        //        using (Bitmap bitmap = eventArgs.Frame.Clone() as Bitmap)
        //        {
        //            VidHeight = bitmap.Height;
        //            VidWidth = bitmap.Width;

        //            if (null == CurrentPicture || CurrentPicture.IsFrozen)
        //            {
        //                System.Windows.Media.PixelFormat aMediaPixelFormat = PixelFormats.Rgb24; //new System.Windows.Media.PixelFormat();
        //                //aMediaPixelFormat = 
        //                theCurrentPicture = new WriteableBitmap(VidWidth, VidHeight, bitmap.HorizontalResolution, bitmap.VerticalResolution, aMediaPixelFormat, null);
        //            }
        //            BitmapData data = bitmap.LockBits(theVideoPixelRectangleInfo, ImageLockMode.ReadOnly, bitmap.PixelFormat);
        //            int inputbufferlength = Math.Abs(data.Stride) * data.Height;


        //            //theCurrentPicture.WritePixels(new Int32Rect(0, 0, VidWidth, VidHeight),  data.Scan0, inputbufferlength, data.Stride, 0, 0);
        //            theCurrentPicture.Lock();
        //            AForge.SystemTools.CopyUnmanagedMemory(theCurrentPicture.BackBuffer, data.Scan0, inputbufferlength);
        //            theCurrentPicture.AddDirtyRect(new Int32Rect(0, 0, VidWidth, VidHeight));
        //            theCurrentPicture.Unlock();

        //            bitmap.UnlockBits(data);
        //        }

        //        RaisePropertyChanged(() => CurrentPicture);
        //    }
        //    catch (Exception ex)
        //    {
        //        if (null != ex)
        //        {
        //            //catch your error here
        //        }
        //    }
        //}
        private static BitmapImage ToWpfBitmap(Bitmap bitmap)
        {
            using (MemoryStream stream = new MemoryStream())
            {
                bitmap.Save(stream, ImageFormat.Bmp);

                stream.Position = 0;
                BitmapImage result = new BitmapImage(); //try this directly for XAML instead of BitmapSource?
                result.BeginInit();
                // According to MSDN, "The default OnDemand cache option retains access to the stream until the image is needed."
                // Force the bitmap to load right now so we can dispose the stream.
                result.CacheOption = BitmapCacheOption.OnLoad;
                result.StreamSource = stream;
                result.EndInit();
                result.Freeze();
                return result;
            }
        }
        #endregion

        #region ProcessFramerateInfo
        private Stopwatch frameclock = new Stopwatch();
        private double VidFramesRcvd(int value)
        {
            double fps;
            if (frameclock.IsRunning)
            {
                frameclock.Stop();
            }
            if (value > 1)
            {
                throw new InvalidOperationException(string.Format("{0} frames received", value));
            }
            try
            {
                theAveragedFPS.AddValue(frameclock.Elapsed.Ticks);
                fps = Convert.ToDouble(TimeSpan.TicksPerSecond) / theAveragedFPS.MovingAverage;
            }
            catch (DivideByZeroException ex)
            {
                fps = double.PositiveInfinity;
            }
            frameclock.Reset();
            frameclock.Start();
            return fps;
        }
        private FastMovingAverageDouble theAveragedFPS = new FastMovingAverageDouble(100);
        #endregion
    }
}
