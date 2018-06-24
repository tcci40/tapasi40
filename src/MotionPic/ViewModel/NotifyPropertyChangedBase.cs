using System;
using System.ComponentModel;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace MotionPic.ViewModel
{
    public abstract class NotifyPropertyChangedBase : INotifyPropertyChanged
    {
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
        protected static string GetPropertyName<T>(System.Linq.Expressions.Expression<Func<T>> propertyExpression)
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
    }
}
