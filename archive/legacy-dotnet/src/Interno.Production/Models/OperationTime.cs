using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class OperationTime
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public Guid Guid { get; set; }
        //public int RoutId { get; set; }
        //public virtual Rout Rout { get; set; }
        public int Keying { get; set; }
        [Required]
        public string Product { get; set; }
        [Required]
        public string Description { get; set; }
        public string WarehouseCode { get; set; }
        public virtual Interno.Inventory.Models.Warehouse Warehouse { get; set; }
        [Required]
        public string Operation { get; set; }
        public int Operators { get; set; }
        [MaxLength (100)]
        public string WorkControl { get; set; }//Pending
        [Required]
        public TimeSpan RunTime { get; set; }
        [Required]
        public TimeSpan SetTime { get; set; }
        public double Hours { get; set; }
        public double LMPU { get; set; }
        public double Inprovement { get; set; }
        public decimal OffSet { get; set; }
        public int Repeat { get; set; }
        public decimal Cost { get; set; }
        //Data Info
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;
        [MaxLength (100)]
        public string Username { get; set; }
        public OperationTime(){ Guid = Guid.NewGuid(); }
    }
}