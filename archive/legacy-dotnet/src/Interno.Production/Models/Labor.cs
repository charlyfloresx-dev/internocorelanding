using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Labor
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public int EmployeeNumber { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Employee Employee { get; set; }
        public string ResourceCode{ get; set; }
        [NotMapped]
        public virtual Models.Resource Resource { get; set; }
        [Required]
        public DateTime Start { get; set; }
        public DateTime End { get; set; }
        public int TypeId { get; set; }
        [NotMapped]
        public virtual LaborType Type { get; set; }
        public virtual TimeSpan Transcurred { get{ return (this.End != DateTime.MinValue)? this.End - this.Start : TimeSpan.Zero;} }
        public virtual int ResultId {get; set;}
        public virtual Result Result { get; set;}
    }

    public class LaborType : Issue // Tipo de Checada
    {
        
    }
}