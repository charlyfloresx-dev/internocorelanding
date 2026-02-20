using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class Users
    {
        public Users(){
            this.isMapped = true;
            this.Claims = new HashSet<InternoClaim>();
        }
        public string Email { get; set; }
        [Key]
        public string UserName { get; set; }
        public string DisplayName { get; set; }
        public bool isMapped { get; set; }

        public virtual ICollection<InternoClaim> Claims {get; set;}
    }

    public partial class InternoClaim
    {
        [Key]
        public int Id { get; set; }
        
        [Required]
        public Users User { get; set; }
     
        public string UserUserName { get; set; }
    
        [Required]
        public InternoRoles InternoRole { get; set; }
    
        [Required]
        public string Claim { get; set; }
    }

    public class IClaim {
        [Required]
        public string Claim { get; set; }
    }
    
    public enum InternoRoles{
        Administrator = 1,
        Manager = 2,
        Supervisor = 3,
        Editor = 4,
        Creator = 5,
        Viewer = 6
    }
}