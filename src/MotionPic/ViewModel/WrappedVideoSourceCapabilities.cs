using AForge.Video.DirectShow;
using System;
using System.ComponentModel;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace MotionPic.ViewModel
{
   
    public class WrappedVideoSourceCapabilities : INotifyPropertyChanged
    {
        private VideoCapabilities theWrappedVidCap = null;

        #region INotifyPropertyChanged implementation
        public event PropertyChangedEventHandler PropertyChanged;
        protected void OnPropertyChanged([CallerMemberName] string propertyName = "")
        {
            if (PropertyChanged != null)
            {
                PropertyChanged(this, new PropertyChangedEventArgs(propertyName));
            }
        }
        protected virtual void RaisePropertyChanged<T>(Expression<Func<T>> propertyExpression)
        {
            var eventHandler = PropertyChanged;
            if (eventHandler != null)
            {
                string propertyName = GetPropertyName(propertyExpression);
                eventHandler(this, new PropertyChangedEventArgs(propertyName));
            }
        }
        /// <summary> 
        /// Extracts the name of a property from an expression. 
        /// </summary> 
        /// <typeparam name="T">The type of the property.</typeparam> 
        /// <param name="propertyExpression">An expression returning the property's name.</param> 
        /// <returns>The name of the property returned by the expression.</returns> 
        /// <exception cref="T:System.ArgumentNullException">If the expression is null.</exception> 
        /// <exception cref="T:System.ArgumentException">If the expression does not represent a property.</exception> 
        protected static string GetPropertyName<T>(Expression<Func<T>> propertyExpression)
        {
            if (propertyExpression == null)
            {
                throw new ArgumentNullException("propertyExpression");
            }
            MemberExpression body = propertyExpression.Body as MemberExpression;
            if (body == null)
            {
                throw new ArgumentException("Invalid argument", "propertyExpression");
            }
            PropertyInfo member = body.Member as PropertyInfo;
            if (member == null)
            {
                throw new ArgumentException("Argument is not a property", "propertyExpression");
            }
            return member.Name;
        }


        #endregion INotifyPropertyChanged implementation
        public static PropertyDescriptorCollection GetPropertyDescriptors()
        {
            return TypeDescriptor.GetProperties(typeof(WrappedVideoSourceCapabilities));
        }
        // private VideoCapabilities aCapabilityItem;

        public VideoCapabilities VideoSourceCapabilities
        {
            get { return theWrappedVidCap; }
            set
            {
                if (null == value)
                {
                    theWrappedVidCap = null;
                    return;
                }
                else
                {
                    if (null != theWrappedVidCap && theWrappedVidCap.Equals(value)) return;
                    theWrappedVidCap = value;
                    updateWrappedProperties();
                }
                OnPropertyChanged();
            }
        }
        private void updateWrappedProperties()
        {
            //AverageFrameRate = theWrappedVidCap.AverageFrameRate;
            //RaisePropertyChanged(() => AverageFrameRate);
            BitCount = theWrappedVidCap.BitCount;
            RaisePropertyChanged(() => BitCount);
            FrameSize = theWrappedVidCap.FrameSize;
            RaisePropertyChanged(() => FrameSize);
            MaximumFrameRate = theWrappedVidCap.MaximumFrameRate;
            RaisePropertyChanged(() => MaximumFrameRate);
        }
        //
        // Summary:
        //     Average frame rate of video device for corresponding AForge.Video.DirectShow.VideoCapabilities.FrameSize.
        // OBSOLETE
        //public int AverageFrameRate { get; private set; }
        //
        // Summary:
        //     Number of bits per pixel provided by the camera.
        public int BitCount { get; private set; }
        //
        // Summary:
        //     Frame size supported by video device.
        public System.Drawing.Size FrameSize { get; private set; }
        //
        // Summary:
        //     Maximum frame rate of video device for corresponding AForge.Video.DirectShow.VideoCapabilities.FrameSize.
        public int MaximumFrameRate { get; private set; }

        //
        // Summary:
        //     Check if the video capability equals to the specified object.
        //
        // Parameters:
        //   obj:
        //     Object to compare with.
        //
        // Returns:
        //     Returns true if both are equal are equal or false otherwise.
        public override bool Equals(object obj)
        {
            // Check if the object is of the same class.
            // The initial null check is unnecessary as the cast will result in null
            // if obj is null to start with.
            var castobj = obj as WrappedVideoSourceCapabilities;

            if (castobj == null)
            {
                // If it is null then it is not equal to this instance.
                return false;
            }

            // Instances are considered equal if the ReferenceId matches.
            //return this.ReferenceId == castobj.ReferenceId;

            return Equals(castobj);
        }
        //
        // Summary:
        //     Check if two video capabilities are equal.
        //
        // Parameters:
        //   vc2:
        //     Second video capability to compare with.
        //
        // Returns:
        //     Returns true if both video capabilities are equal or false otherwise.
        public bool Equals(WrappedVideoSourceCapabilities vc2)
        {
            if ((object)vc2 == null || vc2.theWrappedVidCap == null || theWrappedVidCap == null)
            {
                return false;
            }
            return theWrappedVidCap.Equals(vc2.theWrappedVidCap);
        }
        //
        // Summary:
        //     Get hash code of the object.
        //
        // Returns:
        //     Returns hash code ot the object
        public override int GetHashCode()
        {
            return FrameSize.GetHashCode() ^ BitCount ^ MaximumFrameRate;
        }

        //
        // Summary:
        //     Equality operator.
        //
        // Parameters:
        //   a:
        //     First object to check.
        //
        //   b:
        //     Seconds object to check.
        //
        // Returns:
        //     Return true if both objects are equal or false otherwise.
        public static bool operator ==(WrappedVideoSourceCapabilities a, WrappedVideoSourceCapabilities b)
        {
            // if both are null, or both are same instance, return true.
            if (ReferenceEquals(a, b))
            {
                return true;
            }

            // if one is null, but not both, return false. huh?
            if (((object)a == null) || ((object)b == null))
            {
                return false;
            }

            return a.Equals(b);
        }
        //
        // Summary:
        //     Inequality operator.
        //
        // Parameters:
        //   a:
        //     First object to check.
        //
        //   b:
        //     Seconds object to check.
        //
        // Returns:
        //     Return true if both objects are not equal or false otherwise.
        public static bool operator !=(WrappedVideoSourceCapabilities a, WrappedVideoSourceCapabilities b)
        {
            return !(a == b);
        }

        public WrappedVideoSourceCapabilities()
        {

        }

        public WrappedVideoSourceCapabilities(VideoCapabilities aCapabilityItem)
        {
            theWrappedVidCap = aCapabilityItem;
            updateWrappedProperties();
        }
    }
}
