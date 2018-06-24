using AForge.Video.DirectShow;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace MotionPic.ViewModel
{
    public class ObservableVidSource : ObservableCollection<FilterInfo>
    {
        private FilterInfoCollection theFilterInfoCollection;
        public ObservableVidSource()
        {
            theFilterInfoCollection = new FilterInfoCollection(FilterCategory.VideoInputDevice);
            AddItems();
        }
        public void syncSources()
        {
            theFilterInfoCollection = new FilterInfoCollection(FilterCategory.VideoInputDevice);
            RemoveItems();
            AddItems();
        }
        private void AddItems()
        {
            bool changed = false;

            foreach (FilterInfo aItem in theFilterInfoCollection)
            {
                if (Items.Any(x => x.MonikerString.Equals(aItem.MonikerString))) continue;

                Add(aItem);

                changed = true;
            }
            //    if (changed) OnCollectionChanged(new System.Collections.Specialized.NotifyCollectionChangedEventArgs())
        }
        private void RemoveItems()
        {
            bool changed = false;
            if (theFilterInfoCollection.Count > 0)
            {
                IList<FilterInfo> FilterInfos = FilterInfoIList(theFilterInfoCollection);
                foreach (FilterInfo aObservableItem in Items)
                {
                    if (FilterInfos.Any(x => x.MonikerString.Equals(aObservableItem.MonikerString))) continue;
                    Items.Remove(aObservableItem);
                    changed = true;
                }
            }
        }
        private static IList<FilterInfo> FilterInfoIList(FilterInfoCollection aFilterInfoCollection)
        {
            List<FilterInfo> hmpf = new List<FilterInfo>();
            foreach (FilterInfo aFilterInfoItem in aFilterInfoCollection)
            {
                hmpf.Add(aFilterInfoItem);
            }
            return hmpf;
        }
    }
}

