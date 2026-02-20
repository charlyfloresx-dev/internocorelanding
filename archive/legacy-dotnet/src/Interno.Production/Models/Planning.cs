using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using Interno.Production.Models;
using Interno.Domain;

namespace Interno.Production.Models
{
    public class Planning
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string Line { get; set; }
        [Required]
        public string PartNumber { get; set; }
        public virtual OperationTime OperationTime { get; set; }
        public string Order { get; set; }
        [Required]
        public int OrderQty { get; set; }
        [Required]
        public DateTime ShippingDate { get; set; }
        public string SO { get; set; }
        public string SOLine { get; set; }

        public string PO { get; set; }
        public string altBOM { get; set; }

        public DateTime KitDate { get; set; }
        public Interno.Domain.Enum.StatusType Status { get; set; }
        public DateTime WHSUpdate { get; set; }
        public string Employee { get; set; }
        public virtual Interno.HumanResource.Models.Employee EmployeeData {get;set;}

        public DateTime ReceivedDate { get; set; }

        public string EmployeeReceived { get; set; }
        public virtual Interno.HumanResource.Models.Employee EmployeeReceivedData {get; set;}

        public string Comments { get; set; }
        public string Comments2 { get; set; }
        //Dia de la Semana en Espanol
        public virtual string Dia {get{ return (this.KitDate != DateTime.MinValue)? InternoExtensions.nombreDiasSemana[(int) this.KitDate.DayOfWeek] : null; }}

        public double Hours { get { return (this.OperationTime != null && this.OperationTime.SetTime.TotalHours != 0 && this.OrderQty != 0)? this.OperationTime.SetTime.TotalHours * this.OrderQty : 0;}}
    }
}