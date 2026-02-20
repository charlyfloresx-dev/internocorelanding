using System;
namespace Interno.DJO.Models
{
    public partial class DJOLog
    {
        public int Id { get; set; }
        public string Value1 { get; set; }
        public string Value2 { get; set; }
        public string Value3 { get; set; }
        public DateTime Date { get; set; }
        public string User { get; set; }
        public DJOLogType Type { get; set; }
        public string Comment { get; set; }
        public int IncomingPriorityId {get; set;}
        public virtual IncomingPriority IncomingPriority {get; set;}
    }
}