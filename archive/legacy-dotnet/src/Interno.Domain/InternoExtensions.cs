using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.RegularExpressions;

namespace Interno.Domain
{
    public static partial class InternoExtensions
    {
        static CultureInfo provider = CultureInfo.InvariantCulture;
        public static string[] alphabet = new string[] {"A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"};
        //Fechas en Español
        public static List<string> mesAbreviaciones = new List<string> {"Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"};
        public static List<string> mesNombres = new List<string> {"Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"};
        public static List<string> nombreDiasSemana = new List<string> {"Domingo","Lunes","Martes","Miercoles","Jueves","Viernes","Sabado"};
        public static string getMesAbreviacion(this int monthNumber) => (monthNumber > 0)? mesAbreviaciones[monthNumber-1] : null;
        public static string getMesNombre(this int monthNumber) =>(monthNumber > 0)? mesNombres[monthNumber-1] : null;
        //Fechas desde otro Formato
        public static DateTime FromExcel(this string date) => DateTime.Parse(date,provider);
        public static DateTime FromM3(this string date){//072219
            var month  = date.Substring(0,2);
            var day  = date.Substring(2,2);
            var year  = date.Substring(4,2);
            string fecha = string.Concat(month,"/",day,"/20",year);
            return  DateTime.ParseExact(fecha,"d",provider);
        }

        //* Regresa el numero de Semana en el Mes
        public static int WeekOfMonth(this DateTime date)  
        {  
            DateTime beginningOfMonth = new DateTime(date.Year, date.Month, 1);  
        
            while (date.Date.AddDays(1).DayOfWeek != CultureInfo.CurrentCulture.DateTimeFormat.FirstDayOfWeek)  
                date = date.AddDays(1);  
        
            return (int)Math.Truncate((double)date.Subtract(beginningOfMonth).TotalDays  / 7f) + 1;  
        }

        //* Regresa el numero de Semana del año
        public static int WeekOfYear(this DateTime time)
        {
            // Seriously cheat.  If its Monday, Tuesday or Wednesday, then it'll 
            // be the same week# as whatever Thursday, Friday or Saturday are,
            // and we always get those right
            DayOfWeek day = CultureInfo.InvariantCulture.Calendar.GetDayOfWeek(time);
            if (day >= DayOfWeek.Monday && day <= DayOfWeek.Wednesday)
            {
                time = time.AddDays(3);
            }

            // Return the week of our adjusted day
            return CultureInfo.InvariantCulture.Calendar.GetWeekOfYear(time, CalendarWeekRule.FirstFourDayWeek, DayOfWeek.Monday);
        }
        public static int Quarter(this DateTime time){
            if (time.Month >= 4 && time.Month <= 6)
                return 2;
            else if (time.Month >= 7 && time.Month <= 9)
                return 3;
            else if (time.Month >= 10 && time.Month <= 12)
                return 4;
            else 
                return 1;
        }
        public static DateTime[] GetDatesArray(this DateTime fromDate, DateTime toDate)
        {
            int days = (toDate - fromDate).Days;
            var dates = new DateTime[days];
            for (int i = 0; i < days; i++) dates[i] = fromDate.AddDays(i);
            return dates;
        }

        //Parse Numbers
        // * Elimina caracteres al escanear credencial '11167a' => 11167
        public static int getNumber(this string num) => Int32.Parse(Regex.Match(num,@"\d+").Value);

        public class IDates
        {
            public DateTime From { get; set; }
            public DateTime To { get; set; }
            public string Filter { get; set; }

            public IDates(string from,string to,string filter){
                From = DateTime.Parse(from,provider);
                To = DateTime.Parse(to,provider);
                Filter = Filter;
            }
        }

        public class formatDate
        {
            public DateTime Date { get; set; }
            public string Week {get{ return this.Date.WeekOfYear().ToString("D02"); }}
            public System.DayOfWeek DayOfWeek { get{ return this.Date.DayOfWeek; }}
            public int WeekOfMonth { get{ return this.Date.WeekOfMonth(); }}
            public int Month { get{ return this.Date.Month; }}
            public string MonthName { get{ return this.Month.getMesNombre(); }}
            public int Quarter { get{ return this.Date.Quarter(); }}

            public formatDate(DateTime date)
            {
                Date = date;
            }
        }
    }
}