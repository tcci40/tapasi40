using AForge.Video.DirectShow;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;

namespace MotionPic.ViewModel
{
    public class SortableBindingList<T> : BindingList<T>
    {
        private bool isSortedValue;
        ListSortDirection sortDirectionValue;
        PropertyDescriptor sortPropertyValue;

        public PropertyDescriptorCollection SortableProperties
        {
            get { return TypeDescriptor.GetProperties(typeof(T)); }
        }
        public SortableBindingList() : base() { }
        public SortableBindingList(IList<T> list) : base(list) { }
        protected override void ApplySortCore(PropertyDescriptor prop,
            ListSortDirection direction)
        {
            Type interfaceType = prop.PropertyType.GetInterface("IComparable");
            if (interfaceType == null && prop.PropertyType.IsValueType)
            {
                Type underlyingType = Nullable.GetUnderlyingType(prop.PropertyType);
                if (underlyingType != null)
                {
                    interfaceType = underlyingType.GetInterface("IComparable");
                }
            }
            if (interfaceType != null)
            {
                sortPropertyValue = prop;
                sortDirectionValue = direction;
                IEnumerable<T> query = base.Items;
                if (direction == ListSortDirection.Ascending)
                    query = query.OrderBy(i => prop.GetValue(i));
                else
                    query = query.OrderByDescending(i => prop.GetValue(i));
                int newIndex = 0;
                foreach (object item in query)
                {
                    this.Items[newIndex] = (T)item;
                    newIndex++;
                }
                isSortedValue = true;
                sorting = true;
                this.OnListChanged(new ListChangedEventArgs(ListChangedType.Reset, -1));
                sorting = false;
            }
            else
            {
                throw new NotSupportedException("Cannot sort by " + prop.Name +
                    ". This" + prop.PropertyType.ToString() +
                    " does not implement IComparable");
            }
        }
        bool sorting = false;
        protected override PropertyDescriptor SortPropertyCore
        {
            get { return sortPropertyValue; }
        }
        protected override ListSortDirection SortDirectionCore
        {
            get { return sortDirectionValue; }
        }
        protected override bool SupportsSortingCore
        {
            get { return true; }
        }
        protected override bool IsSortedCore
        {
            get { return isSortedValue; }
        }
        protected override void RemoveSortCore()
        {
            isSortedValue = false;
            sortPropertyValue = null;
        }
        protected override void OnListChanged(ListChangedEventArgs e)
        {
            if (!sorting && sortPropertyValue != null)
                ApplySortCore(sortPropertyValue, sortDirectionValue);
            else
                base.OnListChanged(e);
        }
       
    }
    public class VideoCapabilityCollection : SortableBindingList<WrappedVideoSourceCapabilities>
    {
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
        private void initialsettings()
        {
            AllowEdit = false;
            AllowNew = false;
            AllowRemove = false;
            ApplySortCore(WrappedVideoSourceCapabilities.GetPropertyDescriptors().Find("MaximumFrameRate", false), ListSortDirection.Ascending);
            
        }
        public VideoCapabilityCollection()
        {
            //this.ApplySortCore()
            initialsettings();
        }

        public VideoCapabilityCollection(VideoCaptureDevice aVideoSource)
        {
            initialsettings();
            if (null != aVideoSource)
            {
                if (null != aVideoSource.VideoCapabilities)
                {
                    AddItems(aVideoSource.VideoCapabilities);
                }
            }
            
        }
        public void SyncCaps(VideoCapabilities[] aCapabilityItemsArray)
        {
            AddItems(aCapabilityItemsArray);
            RemoveItems(aCapabilityItemsArray);

        }
        private void AddItems(VideoCapabilities[] aCapabilityItemsArray)
        {
            if (null != aCapabilityItemsArray)
            {
                foreach (VideoCapabilities aCapabilityItem in aCapabilityItemsArray)
                {
                    var foo = new WrappedVideoSourceCapabilities(aCapabilityItem);
                    AddItem(foo);

                }
            }
        }
        private void RemoveItems(VideoCapabilities[] aCapabilityItemsArray)
        {
            if (null == aCapabilityItemsArray || aCapabilityItemsArray.Count() == 0) Items.Clear();
            {
                List<WrappedVideoSourceCapabilities> aRemovalList = new List<WrappedVideoSourceCapabilities>();
                foreach (WrappedVideoSourceCapabilities aCapabilityItem in Items)
                {
                    if (aCapabilityItemsArray.Any(x => x.Equals(aCapabilityItem.VideoSourceCapabilities))) continue;
                    aRemovalList.Add(aCapabilityItem);
                }
                foreach (WrappedVideoSourceCapabilities aCapabilityItem in aRemovalList)
                {
                    RemoveItem(aCapabilityItem);
                }
                
            }
        }
        private void AddItem(WrappedVideoSourceCapabilities aCapabilityItem)
        {
            if (null != aCapabilityItem)
            {
                if (Items.Any(x => x.Equals(aCapabilityItem))) return;
                AllowNew = true;
                Add(aCapabilityItem);
                AllowNew = false;
            }
        }
        private void RemoveItem(WrappedVideoSourceCapabilities aCapabilityItem)
        {
            if (null != aCapabilityItem)
            {
                if (Items.Any(x => x.Equals(aCapabilityItem)))
                {
                    AllowRemove = true;
                    while (Remove(aCapabilityItem)) ;
                    AllowRemove = false;
                }
            }
        }

    }
   
}
